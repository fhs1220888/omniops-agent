# Markdown Skills Design

OmniOps supports Markdown Skills as reusable agent behavior packages.

## Tool vs Runbook vs Skill

| Concept | Purpose | Example | Runtime Role |
| --- | --- | --- | --- |
| Tool | Executable function or API | `query_logs`, `query_metrics`, `query_traces` | Performs an action |
| Runbook | Human-readable operational knowledge | Redis timeout runbook | Retrieved by RAG as guidance |
| Skill | Reusable agent behavior and reasoning method | Redis Timeout Diagnosis Skill | Guides how an agent reasons |

Skills do not execute actions directly. They guide the Report Agent or Reflection Agent on how to use live evidence and tool results.

Observability Profiles decide how live evidence is queried. Skills decide how agents reason about that evidence.

## Why Markdown?

Markdown keeps skills easy to review, version, and extend. A skill is a reusable prompt and workflow package with:

- when to use it
- required evidence
- tools to use
- reasoning steps
- output contract
- guardrails

## Standard Skill Format

```markdown
# Skill Name

## Purpose
## When To Use
## Inputs
## Required Evidence
## Tools To Use
## Reasoning Steps
## Output Contract
## Guardrails
## Example
```

## Evidence Boundary

Skills are not fake data. Skills are not live facts. Skills must not replace Prometheus, Loki, or Tempo evidence.

Guardrail:

```text
Live evidence determines root cause.
Runbooks provide operational knowledge.
Skills provide diagnosis methodology.
If live evidence is insufficient, say evidence insufficient.
```

## How Skills Are Selected

`app/skills/selector.py` uses deterministic keyword scoring. It always includes:

- `evidence_sufficiency_review`
- `rca_report_generation`

It may also select scenario-specific diagnosis skills:

- `redis_timeout_diagnosis`
- `downstream_timeout_diagnosis`
- `mysql_slow_query_diagnosis`
- `application_exception_diagnosis`
- `service_unhealthy_diagnosis`
- `latency_spike_diagnosis`

## API

```text
GET  /api/skills/status
POST /api/skills/select
GET  /api/skills/{skill_id}
```

## How To Add A Skill

1. Create `skills/<skill_id>/SKILL.md`.
2. Fill in all standard sections.
3. Add or update selector keywords if the skill should be automatically selected.
4. Run:
   `uv run pytest -q`
5. Run diagnostic benchmark when live services are available.

## Current Limitation

The first selector is deterministic and keyword-based. It is intentionally stable for tests and CI. Future versions can use embeddings or LLM-assisted selection while keeping the same Skill Registry boundary.
