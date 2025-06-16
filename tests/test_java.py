"""
Java language tests for the code compiler and runner API.
"""

from conftest import wait_for_execution_completion, create_session_client


def test_compile_and_run_java():
    """Test Java compile-then-run workflow."""
    java_code = """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
    # Use session client to maintain cookies
    session_client = create_session_client()

    # Compile first
    compile_resp = session_client.post(
        "/compile",
        data={"language": "java", "code": java_code},
    )
    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    print(f"Java compile response: {compile_data}")
    assert compile_data["success"]

    # Now run using the same session (cookies preserved)
    run_resp = session_client.post(
        "/run",
        data={"language": "java", "code": java_code},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"]
    assert "execution_id" in run_data

    # Verify both requests used the same session_id
    assert run_data["session_id"] is not None
    print(f"Session ID from run response: {run_data['session_id']}")

    # Wait for execution to complete and verify output
    execution_id = run_data["execution_id"]
    result = wait_for_execution_completion(execution_id)
    assert "Hello, World!" in result["output"], f"Unexpected output: {result['output']}"


def test_java_calculator():
    """Test Java code with a simple calculator."""
    java_code = """
public class Calculator {
    public static void main(String[] args) {
        int a = 10;
        int b = 5;
        int sum = a + b;
        int diff = a - b;
        int product = a * b;
        int quotient = a / b;
        
        System.out.println("Sum: " + sum);
        System.out.println("Difference: " + diff);
        System.out.println("Product: " + product);
        System.out.println("Quotient: " + quotient);
    }
}
"""
    # Use session client to maintain cookies
    session_client = create_session_client()

    # Compile first
    compile_resp = session_client.post(
        "/compile",
        data={"language": "java", "code": java_code},
    )
    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    assert compile_data["success"]

    # Now run using the same session (cookies preserved)
    run_resp = session_client.post(
        "/run",
        data={"language": "java", "code": java_code},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"]
    assert "execution_id" in run_data

    # Verify both requests used the same session_id
    assert run_data["session_id"] is not None
    print(f"Session ID from run response: {run_data['session_id']}")

    # Wait for execution to complete and verify output
    execution_id = run_data["execution_id"]
    status_data = wait_for_execution_completion(execution_id)

    # Check for expected calculations in output
    output = status_data["output"]
    assert "Sum: 15" in output
    assert "Difference: 5" in output
    assert "Product: 50" in output
    assert "Quotient: 2" in output
