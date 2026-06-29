from __future__ import annotations

import json
import logging
import os
import random
import time
from datetime import UTC, datetime

import requests
from fastapi import FastAPI, HTTPException, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


SERVICE_NAME = os.getenv("SERVICE_NAME", "order-service")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100").rstrip("/")
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(SERVICE_NAME)

REQUESTS = Counter(
    "order_service_requests_total",
    "Total order-service HTTP requests.",
    ["service", "endpoint", "status"],
)
LATENCY = Histogram(
    "order_service_request_duration_seconds",
    "Order-service request duration.",
    ["service", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)


def _configure_tracing() -> None:
    provider = TracerProvider(
        resource=Resource.create({"service.name": SERVICE_NAME})
    )
    exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


_configure_tracing()
tracer = trace.get_tracer(__name__)
app = FastAPI(title="Order Service Demo")
FastAPIInstrumentor.instrument_app(app)


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    started = time.perf_counter()
    endpoint = request.url.path
    status = "500"
    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    finally:
        REQUESTS.labels(SERVICE_NAME, endpoint, status).inc()
        LATENCY.labels(SERVICE_NAME, endpoint).observe(time.perf_counter() - started)


@app.get("/health")
def health() -> dict:
    _log("health check passed", endpoint="/health")
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/checkout")
def checkout() -> dict:
    with tracer.start_as_current_span("checkout"):
        _sleep(0.02, 0.06)
        _log("checkout completed", endpoint="/checkout")
        return {"status": "ok", "cart_id": random.randint(1000, 9999)}


@app.get("/checkout/slow")
def checkout_slow() -> dict:
    with tracer.start_as_current_span("checkout_slow"):
        _sleep(0.6, 0.9)
        _log("checkout slow path exceeded latency budget", endpoint="/checkout/slow")
        return {"status": "slow", "latency_budget": "exceeded"}


@app.get("/checkout/error")
def checkout_error() -> dict:
    with tracer.start_as_current_span("checkout_error"):
        _sleep(0.04, 0.08)
        _log(
            "checkout failed with upstream payment error",
            endpoint="/checkout/error",
            level="error",
            error_type="PaymentProviderError",
        )
        raise HTTPException(status_code=503, detail="payment provider unavailable")


@app.get("/checkout/redis-timeout")
def checkout_redis_timeout() -> dict:
    with tracer.start_as_current_span("checkout_redis_timeout"):
        _sleep(0.25, 0.4)
        _log(
            "checkout failed: RedisTimeoutException after 250ms",
            endpoint="/checkout/redis-timeout",
            level="error",
            error_type="RedisTimeoutException",
        )
        raise HTTPException(status_code=504, detail="RedisTimeoutException")


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def _sleep(low: float, high: float) -> None:
    time.sleep(random.uniform(low, high))


def _current_trace_id() -> str:
    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return ""
    return f"{span_context.trace_id:032x}"


def _log(
    message: str,
    *,
    endpoint: str,
    level: str = "info",
    error_type: str | None = None,
) -> None:
    trace_id = _current_trace_id()
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "service": SERVICE_NAME,
        "endpoint": endpoint,
        "level": level,
        "message": message,
        "trace_id": trace_id,
    }
    if error_type:
        payload["error_type"] = error_type
    logger.info(json.dumps(payload, sort_keys=True))
    _push_to_loki(payload)


def _push_to_loki(payload: dict) -> None:
    labels = {
        "service": SERVICE_NAME,
        "level": payload["level"],
        "endpoint": payload["endpoint"],
    }
    body = {
        "streams": [
            {
                "stream": labels,
                "values": [
                    [
                        str(time.time_ns()),
                        json.dumps(payload, sort_keys=True),
                    ]
                ],
            }
        ]
    }
    try:
        requests.post(
            f"{LOKI_URL}/loki/api/v1/push",
            json=body,
            timeout=1.0,
        )
    except requests.RequestException:
        logger.warning(
            json.dumps(
                {
                    "service": SERVICE_NAME,
                    "level": "warning",
                    "message": "failed to push log to loki",
                    "trace_id": payload.get("trace_id", ""),
                },
                sort_keys=True,
            )
        )
