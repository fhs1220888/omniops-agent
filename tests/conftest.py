import pytest


@pytest.fixture(autouse=True)
def force_fake_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_FAKE_LLM", "true")
    monkeypatch.setenv("USE_FAKE_TOOLS", "true")
    monkeypatch.setenv("OBSERVABILITY_BACKEND", "fake")
