from fastapi.testclient import TestClient


def test_list_explanations(client: TestClient) -> None:
    r = client.get("/api/explanations")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == "test-id-1"


def test_list_pagination(client: TestClient) -> None:
    r = client.get("/api/explanations?limit=1&offset=0")
    assert r.status_code == 200
    assert r.json()["limit"] == 1


def test_get_explanation(client: TestClient) -> None:
    r = client.get("/api/explanations/test-id-1")
    assert r.status_code == 200
    assert r.json()["source_key"] == "inv-1"


def test_get_explanation_not_found(client: TestClient) -> None:
    r = client.get("/api/explanations/nonexistent")
    assert r.status_code == 404


def test_set_feedback_up(client: TestClient) -> None:
    r = client.patch("/api/explanations/test-id-1/feedback", json={"feedback": "up"})
    assert r.status_code == 200
    assert r.json()["feedback"] == "up"


def test_set_feedback_clear(client: TestClient) -> None:
    client.patch("/api/explanations/test-id-1/feedback", json={"feedback": "up"})
    r = client.patch("/api/explanations/test-id-1/feedback", json={"feedback": None})
    assert r.status_code == 200
    assert r.json()["feedback"] is None


def test_set_feedback_invalid(client: TestClient) -> None:
    r = client.patch("/api/explanations/test-id-1/feedback", json={"feedback": "invalid"})
    assert r.status_code == 422


def test_augment_explanation(client: TestClient) -> None:
    r = client.post("/api/explanations/test-id-1/augment")
    assert r.status_code == 200
    body = r.json()
    assert "augmented_summary" in body
    assert body["model"] == "gpt-4o-mini"


def test_augment_not_found(client: TestClient) -> None:
    r = client.post("/api/explanations/nonexistent/augment")
    assert r.status_code == 404
