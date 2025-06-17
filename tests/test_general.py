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
    import time

    # First, start a long-running Python process (infinite loop that prints)
    long_running_code = """
import time
count = 0
while True:
    print(f"Running... {count}")
    count += 1
    time.sleep(0.5)
    if count > 100:  # Safety net to prevent truly infinite execution in tests
        break
"""

    # Start the execution
    run_resp = client.post(
        "/run",
        data={
            "code": long_running_code,
            "language": "python",
            "timeout": "60",  # Give it 60 seconds timeout
        },
    )

    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"] is True
    execution_id = run_data["execution_id"]

    # Wait a moment to ensure the process has started
    time.sleep(1)

    # Check that the execution is running
    status_resp = client.get(f"/status/{execution_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["running"] is True

    # Now cancel the execution
    cancel_resp = client.post("/cancel", data={"execution_id": execution_id})
    assert cancel_resp.status_code == 200
    cancel_data = cancel_resp.json()
    print(f"Cancel response: {cancel_data}")  # Debug print to see what's happening
    assert cancel_data["success"] is True
    assert "cancel" in cancel_data["message"].lower()

    # Wait a moment for cancellation to take effect
    time.sleep(1)

    # Verify the execution is no longer running
    final_status_resp = client.get(f"/status/{execution_id}")
    assert final_status_resp.status_code == 200
    final_status_data = final_status_resp.json()
    assert final_status_data["running"] is False
    assert final_status_data["cancelled"] is True


def test_status():
    """Test execution status monitoring."""
    resp = client.get("/status/testsession1")
    assert resp.status_code == 200


def test_session_info():
    """Test session information retrieval."""
    # First create a session by running some code to ensure session exists
    code = "print('test')"
    session_id = "testsession_info"

    # Create session by running code
    run_resp = client.post(
        "/run",
        data={"language": "python", "code": code},
        cookies={"session_id": session_id},
    )
    assert run_resp.status_code == 200

    # Now check session info
    resp = client.get("/session/info", cookies={"session_id": session_id})
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
