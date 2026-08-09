import sqlite3

import pytest
from fastapi.testclient import TestClient

from api.auth import create_api_key
from api.deps import get_db
from api.main import app


@pytest.fixture
def client(temp_conn: sqlite3.Connection):
    raw_key = create_api_key(temp_conn, "acme")

    def override_get_db():
        yield temp_conn

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app), raw_key
    app.dependency_overrides.clear()


def test_health_requires_no_auth(client):
    test_client, _ = client
    resp = test_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_property_recommendations_require_api_key(client):
    test_client, _ = client
    resp = test_client.get("/properties/1/recommendations")
    assert resp.status_code == 401


def test_property_recommendations_for_known_property(client):
    test_client, raw_key = client
    resp = test_client.get(
        "/properties/1/recommendations", headers={"X-API-Key": raw_key}
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_property_recommendations_unknown_property_404(client):
    test_client, raw_key = client
    resp = test_client.get(
        "/properties/9999/recommendations", headers={"X-API-Key": raw_key}
    )
    assert resp.status_code == 404


def test_property_recommendations_invalid_id_422(client):
    test_client, raw_key = client
    resp = test_client.get(
        "/properties/0/recommendations", headers={"X-API-Key": raw_key}
    )
    assert resp.status_code == 422


def test_list_recommendations_filters_by_type(client):
    test_client, raw_key = client
    resp = test_client.get(
        "/recommendations",
        params={"type": "pricing"},
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 200
    assert all(r["type"] == "pricing" for r in resp.json())


def test_list_recommendations_rejects_invalid_type(client):
    test_client, raw_key = client
    resp = test_client.get(
        "/recommendations",
        params={"type": "not-a-real-type"},
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 422
