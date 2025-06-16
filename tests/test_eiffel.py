"""
Eiffel language tests for the code compiler and runner API.
"""

from conftest import wait_for_execution_completion, create_session_client
import time


def test_compile_and_run_eiffel():
    """Test Eiffel compile-then-run workflow."""
    code = """class
    HELLO_WORLD

create
    make

feature
    make
            -- Print hello world message
        do
            print ("Hello, Eiffel!%N")
        end

end"""
    session_client = create_session_client()
    compile_resp = session_client.post(
        "/compile",
        data={"language": "eiffel", "code": code},
    )
    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    print(f"Eiffel compile response: {compile_data}")  # Debug output
    assert compile_data["success"]

    # Now run using the same session (cookies preserved)
    run_resp = session_client.post(
        "/run",
        data={"language": "eiffel", "code": code},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"]
    assert "execution_id" in run_data

    # Verify both requests used the same session_id
    assert run_data["session_id"] is not None
    print(f"Session ID from run response: {run_data['session_id']}")

    # Wait for execution to complete
    execution_id = run_data["execution_id"]
    status_data = wait_for_execution_completion(execution_id)

    # Check if execution succeeded, or at least compilation worked
    assert "Hello, Eiffel!" in status_data["output"]
    assert compile_data["success"]  # At least compilation worked


def test_eiffel_with_variables():
    """Test Eiffel code with variables and calculations."""
    code = """class
    CALCULATOR

create
    make

feature
    make
            -- Simple calculation example
        local
            x: INTEGER
            y: INTEGER
            res: INTEGER
        do
            x := 5
            y := 10
            res := x + y
            print ("Result: " + res.out + "%N")
        end

end"""
    session_client = create_session_client()
    compile_resp = session_client.post(
        "/compile",
        data={"language": "eiffel", "code": code},
    )
    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    assert compile_data["success"]

    # Now run using the same session (cookies preserved)
    run_resp = session_client.post(
        "/run",
        data={"language": "eiffel", "code": code},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"]
    assert "execution_id" in run_data

    # Wait for execution to complete
    execution_id = run_data["execution_id"]
    status_data = wait_for_execution_completion(execution_id)

    # Check if execution succeeded, or at least compilation worked
    assert "Result: 15" in status_data["output"]
    assert compile_data["success"]  # At least compilation worked


def test_eiffel_compilation_performance_with_reused_container():
    """Test that compiling Eiffel code twice is much faster the second time due to
    container reuse."""
    eiffel_code = """class
    PERFORMANCE_TEST

create
    make

feature
    make
            -- Test performance with container reuse
        do
            print ("Performance test completed!%N")
        end

end"""

    # Use session client to maintain cookies and session
    session_client = create_session_client()

    # First compilation - container needs to be created
    print("Starting first compilation (container creation)...")
    start_time_1 = time.time()

    compile_resp_1 = session_client.post(
        "/compile",
        data={"language": "eiffel", "code": eiffel_code},
    )

    end_time_1 = time.time()
    first_compile_time = end_time_1 - start_time_1

    assert compile_resp_1.status_code == 200
    compile_data_1 = compile_resp_1.json()
    print(f"First compilation response: {compile_data_1}")

    # Second compilation - container should be reused
    print("Starting second compilation (container reuse)...")
    start_time_2 = time.time()

    compile_resp_2 = session_client.post(
        "/compile",
        data={"language": "eiffel", "code": eiffel_code},
    )

    end_time_2 = time.time()
    second_compile_time = end_time_2 - start_time_2

    assert compile_resp_2.status_code == 200
    compile_data_2 = compile_resp_2.json()
    print(f"Second compilation response: {compile_data_2}")

    # Print timing results
    print(f"First compilation time: {first_compile_time:.3f} seconds")
    print(f"Second compilation time: {second_compile_time:.3f} seconds")

    # The second compilation should be significantly faster (at least 2x faster)
    # This accounts for the container creation overhead in the first compilation
    speed_improvement = first_compile_time / second_compile_time
    print(f"Speed improvement: {speed_improvement:.2f}x")

    # Assert that the second compilation is at least 1.5x faster
    # (allowing some margin for system variations)
    assert speed_improvement >= 1.5, (
        f"Expected second compilation to be at least 1.5x faster, "
        f"but got {speed_improvement:.2f}x improvement. "
        f"First: {first_compile_time:.3f}s, Second: {second_compile_time:.3f}s"
    )

    # Both compilations should succeed
    assert compile_data_1.get("success", False), "First compilation should succeed"
    assert compile_data_2.get("success", False), "Second compilation should succeed"

    print("✅ Container reuse performance test passed!")


def test_eiffel_compile_run_workflow_with_performance():
    """Test the complete compile-then-run workflow and verify container reuse performance."""
    eiffel_code = """class
    WORKFLOW_TEST

create
    make

feature
    make
            -- Test complete workflow with performance
        do
            print ("Workflow test: Hello, Eiffel!%N")
        end

end"""

    session_client = create_session_client()

    # Time the compile step
    print("Timing compile step...")
    compile_start = time.time()
    compile_resp = session_client.post(
        "/compile",
        data={"language": "eiffel", "code": eiffel_code},
    )
    compile_time = time.time() - compile_start

    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    assert compile_data["success"]

    # Time the run step (should be faster since container exists)
    print("Timing run step...")
    run_start = time.time()
    run_resp = session_client.post(
        "/run",
        data={"language": "eiffel", "code": eiffel_code},
    )
    run_time = time.time() - run_start

    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"]
    assert "execution_id" in run_data

    # Verify both requests used the same session_id
    assert run_data["session_id"] is not None
    print(f"Session ID from run response: {run_data['session_id']}")

    # Wait for execution to complete
    execution_id = run_data["execution_id"]
    status_data = wait_for_execution_completion(execution_id)

    # Print timing results
    print(f"Compile time: {compile_time:.3f} seconds")
    print(f"Run time: {run_time:.3f} seconds")

    # The run step should be faster than compile (no container creation)
    assert run_time < compile_time, (
        f"Run step should be faster than compile step. "
        f"Compile: {compile_time:.3f}s, Run: {run_time:.3f}s"
    )

    # Check if execution succeeded
    assert "Hello, Eiffel!" in status_data["output"]
    print("✅ Execution output verified")
    assert compile_data["success"]

    print("✅ Complete workflow with performance test passed!")


def test_eiffel_verification_success():
    """Test Eiffel code verification with a successful check."""
    code = """class
    HELLO_WORLD

create
    make

feature
    make
        do
            check True end
        end

end"""
    session_client = create_session_client()
    
    # Test verification endpoint
    verify_resp = session_client.post(
        "/verify",
        data={"language": "eiffel", "code": code},
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    print(f"Eiffel verification response: {verify_data}")
    assert verify_data["success"]
    assert "execution_id" in verify_data

    # Wait for verification to complete
    execution_id = verify_data["execution_id"]
    status_data = wait_for_execution_completion(execution_id)

    # Check if verification succeeded
    assert status_data.get("success", False), (
        f"Verification should succeed, but got: {status_data.get('output', '')}"
    )
    print("✅ Verification successful for 'check True'")


def test_eiffel_verification_failure():
    """Test Eiffel code verification with a failing check."""
    code = """class
    HELLO_WORLD

create
    make

feature
    make
        do
            check False end
        end

end"""
    session_client = create_session_client()
    
    # Test verification endpoint
    verify_resp = session_client.post(
        "/verify",
        data={"language": "eiffel", "code": code},
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    print(f"Eiffel verification response: {verify_data}")
    assert verify_data["success"]  # The verification process should start successfully
    assert "execution_id" in verify_data

    # Wait for verification to complete
    execution_id = verify_data["execution_id"]
    status_data = wait_for_execution_completion(execution_id)

    # Check if verification failed (as expected for 'check False')
    assert not status_data.get("success", True), (
        f"Verification should fail for 'check False', "
        f"but got: {status_data.get('output', '')}"
    )
    print("✅ Verification correctly failed for 'check False'")


def test_eiffel_verification_unsupported_language():
    """Test that verification endpoint rejects non-Eiffel languages."""
    code = """print("Hello, World!")"""
    session_client = create_session_client()
    
    # Test verification endpoint with Python code
    verify_resp = session_client.post(
        "/verify",
        data={"language": "python", "code": code},
    )
    assert verify_resp.status_code == 400  # Should return bad request
    verify_data = verify_resp.json()
    print(f"Python verification response: {verify_data}")
    assert "not supported" in verify_data["detail"].lower()
    print("✅ Verification correctly rejected for non-Eiffel language")
