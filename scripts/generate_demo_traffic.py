"""Generate real HTTP traffic for the local order-service demo."""

from __future__ import annotations

from collections import Counter
import json
import os
import time

import httpx


ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002").rstrip("/")


def main() -> None:
    paths = (
        ["/checkout"] * 20
        + ["/checkout/slow"] * 5
        + ["/checkout/error"] * 4
        + ["/checkout/redis-timeout"] * 4
    )
    counts: Counter[str] = Counter()
    for path in paths:
        try:
            response = httpx.get(f"{ORDER_SERVICE_URL}{path}", timeout=5.0)
            counts[f"{path}:{response.status_code}"] += 1
        except Exception as exc:
            counts[f"{path}:error:{type(exc).__name__}"] += 1
        time.sleep(0.05)
    print(
        json.dumps(
            {
                "order_service_url": ORDER_SERVICE_URL,
                "request_count": len(paths),
                "status_counts": dict(sorted(counts.items())),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
