# Evidence Sufficiency Review Skill

## Purpose

Guide Reflection Agent and Report Agent behavior when judging whether evidence is sufficient for RCA.

## When To Use

Always use this skill during reflection or report generation.

## Inputs

- Evidence items from logs, metrics, and traces.
- Failed tools, skipped tools, denied tools, and approval-required tools.
- Confidence scores and root cause candidate.

## Required Evidence

- Enough evidence examples:
  - Metrics anomaly plus matching log event plus matching trace span.
  - Strong log error plus matching metric spike.
  - Trace bottleneck plus matching latency metric.
- Insufficient evidence examples:
  - No logs, no metrics, and no traces.
  - Only a generic symptom.
  - Only a runbook or skill match but no live evidence.

## Tools To Use

- No direct tool execution. Use existing evidence and tool metadata.

## Reasoning Steps

1. Count non-empty evidence items.
2. Identify missing evidence sources.
3. Check whether failed or timed-out tools block critical evidence.
4. Treat runbooks and skills as guidance only.
5. Recommend next queries when evidence is insufficient.

## Output Contract

Return `sufficient` or `insufficient`, missing evidence, and recommended next queries.

## Guardrails

- Do not let skills or runbooks substitute for live evidence.
- Do not guess root cause when evidence is empty.
- Policy-blocked evidence must be listed as a limitation.

## Example

If metrics, logs, and traces are all empty for `unknown-service`, mark evidence insufficient and recommend checking service naming and backend reachability.
