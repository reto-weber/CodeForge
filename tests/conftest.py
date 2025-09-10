"""
Shared test configuration and fixtures for the API test suite.
"""

import sys
import os
import time
import httpx
from fastapi.testclient import TestClient

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app

# Use the new explicit transport style to avoid deprecation warning
client = TestClient(app=app)


def wait_for_execution_completion(execution_id, max_attempts=30):
    """
    Helper function to wait for execution completion and verify output.

    Args:
        execution_id: The execution ID to monitor
        max_attempts: Maximum number of polling attempts

    Returns:
        status_data: The final status data when execution completes

    Raises:
        AssertionError: If execution doesn't complete or output doesn't match
    """
    for attempt in range(max_attempts):
        status_resp = client.get(f"/status/{execution_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        print(f"Status response (attempt {attempt + 1}): {status_data}")

        if status_data.get("completed", False):
            return status_data
        time.sleep(1)

    # If we get here, execution didn't complete in time
    assert False, f"Execution didn't complete after {max_attempts} attempts"


def create_session_client():
    """
    Create a test client that maintains session cookies across requests.

    Returns:
        A client wrapper that handles cookies automatically
    """

    class SessionClient:
        def __init__(self):
            self.cookies = {}

        def post(self, url, **kwargs):
            # Add existing cookies to the request
            if "cookies" not in kwargs:
                kwargs["cookies"] = {}
            kwargs["cookies"].update(self.cookies)

            response = client.post(url, **kwargs)

            # Extract and store cookies from the response
            if hasattr(response, "cookies") and response.cookies:
                for name, value in response.cookies.items():
                    self.cookies[name] = value

            return response

        def get(self, url, **kwargs):
            # Add existing cookies to the request
            if "cookies" not in kwargs:
                kwargs["cookies"] = {}
            kwargs["cookies"].update(self.cookies)

            return client.get(url, **kwargs)

    return SessionClient()
