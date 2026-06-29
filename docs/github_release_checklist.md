# GitHub Release Checklist

Use this checklist before publishing a demo or resume-ready release.

## Local Safety

- Confirm `.env` is not tracked:
  `git ls-files | grep '^.env$' || true`
- Confirm `.env.live.example` does not contain a real `LLM_API_KEY`.
- Run tests:
  `uv run pytest -q`
- Run repository safety checks:
  `uv run python scripts/check_repo_safety.py`
- Run the live demo when Docker and OmniOps API are available:
  `bash scripts/demo_live.sh`

## GitHub Push

- Push the main branch:
  `git push origin main`
- Push tags:
  `git push origin --tags`
- Confirm GitHub Actions CI passes.
- Confirm README badges render correctly.
- Confirm README Mermaid diagrams render correctly.

## Public Portfolio Review

- Check that no secrets, local `.env`, logs, caches, or Docker volume data are tracked.
- Confirm screenshots or output snippets do not expose API keys.
- If using this as a public resume project, change the GitHub repository from private to public only after CI passes.
- Verify the live demo instructions still match the current Docker compose and scripts.
