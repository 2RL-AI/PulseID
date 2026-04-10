"""Backend API tests (uses SQLite in-memory for isolation)."""

import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["PULSEID_API_KEY"] = "test-key"
os.environ["PULSEID_USERNAME"] = "testadmin"
os.environ["PULSEID_PASSWORD"] = "testpass"
os.environ["PULSEID_SECRET_KEY"] = "test-secret-key-min-32-chars!!"

import pytest

from app import create_app, db as _db
from app.reader import reader_service


@pytest.fixture(autouse=True)
def _stop_reader():
    """Prevent the background reader thread from starting during tests."""
    reader_service.stop()
    yield
    reader_service.stop()


@pytest.fixture()
def app():
    application = create_app()
    application.config["TESTING"] = True
    reader_service.stop()
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def api_headers():
    return {"X-API-Key": "test-key", "Content-Type": "application/json"}


@pytest.fixture()
def auth_headers(client, api_headers):
    resp = client.post(
        "/api/auth/login",
        json={"username": "testadmin", "password": "testpass"},
        headers=api_headers,
    )
    token = resp.get_json()["token"]
    return {**api_headers, "Authorization": f"Bearer {token}"}


# ── Auth ───────────────────────────────────────────────────

class TestAuth:
    def test_login_success(self, client, api_headers):
        resp = client.post("/api/auth/login", json={"username": "testadmin", "password": "testpass"}, headers=api_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "token" in data
        assert data["username"] == "testadmin"

    def test_login_wrong_password(self, client, api_headers):
        resp = client.post("/api/auth/login", json={"username": "testadmin", "password": "wrong"}, headers=api_headers)
        assert resp.status_code == 401

    def test_login_missing_user(self, client, api_headers):
        resp = client.post("/api/auth/login", json={"username": "nobody", "password": "x"}, headers=api_headers)
        assert resp.status_code == 401

    def test_me(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["username"] == "testadmin"

    def test_me_no_token(self, client, api_headers):
        resp = client.get("/api/auth/me", headers=api_headers)
        assert resp.status_code == 401


# ── API key protection ─────────────────────────────────────

class TestApiKeyProtection:
    def test_no_api_key(self, client):
        resp = client.get("/api/employees")
        assert resp.status_code == 401

    def test_wrong_api_key(self, client):
        resp = client.get("/api/employees", headers={"X-API-Key": "wrong"})
        assert resp.status_code == 401


# ── Employees CRUD ─────────────────────────────────────────

class TestEmployees:
    def test_list_empty(self, client, auth_headers):
        resp = client.get("/api/employees", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_create(self, client, auth_headers):
        resp = client.post("/api/employees", json={"first_name": "Alice", "last_name": "Test"}, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Test"
        assert data["full_name"] == "Alice Test"
        assert data["id"] is not None

    def test_create_missing_fields(self, client, auth_headers):
        resp = client.post("/api/employees", json={"first_name": "Alice"}, headers=auth_headers)
        assert resp.status_code == 400

    def test_get(self, client, auth_headers):
        resp = client.post("/api/employees", json={"first_name": "Bob", "last_name": "Smith", "email": "bob@test.com"}, headers=auth_headers)
        eid = resp.get_json()["id"]
        resp = client.get(f"/api/employees/{eid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["email"] == "bob@test.com"

    def test_update(self, client, auth_headers):
        resp = client.post("/api/employees", json={"first_name": "X", "last_name": "Y"}, headers=auth_headers)
        eid = resp.get_json()["id"]
        resp = client.put(f"/api/employees/{eid}", json={"first_name": "Updated"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["first_name"] == "Updated"

    def test_delete(self, client, auth_headers):
        resp = client.post("/api/employees", json={"first_name": "A", "last_name": "B"}, headers=auth_headers)
        eid = resp.get_json()["id"]
        resp = client.delete(f"/api/employees/{eid}", headers=auth_headers)
        assert resp.status_code == 200
        resp = client.get(f"/api/employees/{eid}", headers=auth_headers)
        assert resp.status_code == 404

    def test_not_found(self, client, auth_headers):
        resp = client.get("/api/employees/9999", headers=auth_headers)
        assert resp.status_code == 404


# ── Users CRUD ─────────────────────────────────────────────

class TestUsers:
    def test_list(self, client, auth_headers):
        resp = client.get("/api/users", headers=auth_headers)
        assert resp.status_code == 200
        users = resp.get_json()
        assert any(u["username"] == "testadmin" for u in users)

    def test_create_user(self, client, auth_headers):
        resp = client.post("/api/users", json={"username": "newuser", "password": "pass1234"}, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.get_json()["username"] == "newuser"

    def test_create_duplicate(self, client, auth_headers):
        client.post("/api/users", json={"username": "dup", "password": "pass1234"}, headers=auth_headers)
        resp = client.post("/api/users", json={"username": "dup", "password": "pass1234"}, headers=auth_headers)
        assert resp.status_code == 409

    def test_update_user(self, client, auth_headers):
        resp = client.post("/api/users", json={"username": "edit_me", "password": "pass1234"}, headers=auth_headers)
        uid = resp.get_json()["id"]
        resp = client.put(f"/api/users/{uid}", json={"username": "edited"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["username"] == "edited"

    def test_delete_user(self, client, auth_headers):
        resp = client.post("/api/users", json={"username": "del_me", "password": "pass1234"}, headers=auth_headers)
        uid = resp.get_json()["id"]
        resp = client.delete(f"/api/users/{uid}", headers=auth_headers)
        assert resp.status_code == 200


# ── Records ────────────────────────────────────────────────

class TestRecords:
    def test_list_empty(self, client, auth_headers):
        resp = client.get("/api/records", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["records"] == []

    def test_latest_empty(self, client, auth_headers):
        resp = client.get("/api/records/latest", headers=auth_headers)
        assert resp.status_code == 200
        assert "server_time" in resp.get_json()

    def test_available_months_empty(self, client, auth_headers):
        resp = client.get("/api/available-months", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["months"] == []


# ── Reader ─────────────────────────────────────────────────

class TestReader:
    def test_status(self, client, auth_headers):
        resp = client.get("/api/reader/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "reader_connected" in data
        assert "pcscd_available" in data

    def test_detect(self, client, auth_headers):
        resp = client.get("/api/reader/detect", headers=auth_headers)
        assert resp.status_code == 200
        assert "readers" in resp.get_json()
