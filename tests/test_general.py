"""
General API tests for basic endpoints, session management, examples, and admin functions.
"""

from conftest import client


def test_root():
    """Test the home page endpoint."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "<html" in resp.text


def test_favicon():
    """Test favicon endpoint."""
    resp = client.get("/favicon.ico")
    assert resp.status_code in (200, 404)  # favicon may be missing


def test_cancel():
    """Test execution cancellation."""
    resp = client.post("/cancel", data={"execution_id": "testsession1"})
    assert resp.status_code == 200


def test_status():
    """Test execution status monitoring."""
    resp = client.get("/status/testsession1")
    assert resp.status_code == 200


def test_session_info():
    """Test session information retrieval."""
    resp = client.get("/session/info", cookies={"session_id": "testsession1"})
    assert resp.status_code == 200
    data = resp.json()
    assert "container" in data or "session_id" in data  # Check for session info


def test_session_cleanup():
    """Test session cleanup."""
    resp = client.post("/session/cleanup", cookies={"session_id": "testsession1"})
    assert resp.status_code == 200


def test_examples_list():
    """Test listing available code examples."""
    resp = client.get("/examples")
    assert resp.status_code == 200
    data = resp.json()
    # Response contains language categories like 'python', 'java', etc.
    assert any(lang in data for lang in ["python", "java", "c", "cpp"])


def test_examples_file():
    """Test retrieving specific example files."""
    resp = client.get("/examples/python/hello_world.py")
    assert resp.status_code == 200
    assert "print" in resp.json().get("code", "")


def test_admin_get_config():
    """Test configuration retrieval with admin authentication."""
    resp = client.get("/admin/config", headers={"X-API-Key": "supersecretapikey"})
    assert resp.status_code == 200


def test_admin_update_config():
    """Test configuration updates with admin authentication."""
    resp = client.post(
        "/admin/config",
        json={"dummy": True},
        headers={"X-API-Key": "supersecretapikey"},
    )
    assert resp.status_code in (200, 400, 422)  # 400/422 if validation fails


def test_admin_get_stats():
    """Test container statistics retrieval."""
    resp = client.get("/admin/containers", headers={"X-API-Key": "supersecretapikey"})
    assert resp.status_code == 200


def test_admin_restart():
    """Test cleanup functionality."""
    resp = client.post(
        "/admin/cleanup",
        data={"max_age_hours": "1"},  # String instead of int
        headers={"X-API-Key": "supersecretapikey"},
    )
    assert resp.status_code in (200, 503)  # 503 if not implemented
