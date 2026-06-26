from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_root_returns_index_html() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "OmniOps Agent" in response.text
