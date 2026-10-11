from fastapi.testclient import TestClient

from mission_control.api.app import create_app


def test_m0_health_returns_200_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
