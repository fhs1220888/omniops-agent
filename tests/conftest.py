import pytest


@pytest.fixture(autouse=True)
def force_fake_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_FAKE_LLM", "true")
