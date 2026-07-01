# Application Exception Diagnosis Skill

## Purpose

Guide an agent through diagnosing application exception and HTTP 500 spikes.

## When To Use

Use this skill when the incident mentions application exception, HTTP 500, stack trace, null state, validation error, or code path failure.

## Inputs

- Incident title, service, and symptom.
- Prometheus error rate and status metrics.
- Loki exception logs.
- Tempo failed spans.

## Required Evidence

- Prometheus: 500 rate or error rate spike.
- Loki: `application_exception`, `exception_type`, error message, or stack trace.
- Tempo: failed span or span status error.

## Tools To Use

- `query_metrics`
- `query_logs`
- `query_traces`

## Reasoning Steps

1. Confirm HTTP 500 rate in metrics.
2. Inspect logs for exception type and error message.
3. Correlate trace ID to failed spans.
4. Check recent code path or deployment if evidence points to application logic.
5. If no live exception evidence exists, report evidence insufficient.

## Output Contract

Return an application exception RCA with exception type, impact, evidence IDs, and recommended rollback or fix path when supported by evidence.

## Guardrails

- Do not invent a stack trace.
- Do not blame code without log or trace support.
- Skills are reasoning guidance only.

## Example

When metrics show 500s and logs contain `application_exception` with an exception type, diagnose application-level failure and recommend rollback, input validation, or code guard fixes.
