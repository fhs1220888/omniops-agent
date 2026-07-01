# RCA Report Generation Skill

## Purpose

Guide the Report Agent in producing structured, evidence-grounded RCA output.

## When To Use

Always use this skill when generating an RCA report.

## Inputs

- Incident metadata.
- Investigation plan.
- Evidence items and evidence graph.
- Tool traces and agent traces.
- Retrieved runbooks and selected skills.

## Required Evidence

- Root cause must be supported by live logs, metrics, traces, or explicit evidence insufficiency.
- Retrieved runbooks are operational knowledge.
- Skills are diagnosis methodology.

## Tools To Use

- No direct tool execution. Use gathered evidence and retrieved guidance.

## Reasoning Steps

1. Summarize incident and impact.
2. State root cause only if grounded in live evidence.
3. List evidence IDs and source types.
4. Explain confidence and missing evidence.
5. Recommend actions with owners and priorities.
6. Include policy limitations and approval requirements.

## Output Contract

The report should include Summary, Root Cause, Evidence, Impact, Confidence, Recommended Actions, and Missing Evidence / Limitations.

## Guardrails

- No fake fallback in real mode.
- No overclaiming.
- Do not infer root cause only from skills or runbooks.
- If live evidence is insufficient, say evidence insufficient.

## Example

If logs show `downstream_timeout`, metrics show 504s, and traces show `payment-service.call` slow, produce a downstream timeout RCA with evidence IDs and mitigation steps.
