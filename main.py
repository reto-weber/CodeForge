import os
import json
import subprocess
import tempfile
import threading
import time
import signal
from typing import Dict, Any

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Global variables for process management
active_processes = {}
process_counter = 0

app = FastAPI(title="Code Compiler and Runner")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Load configuration
def load_config():
    try:
        with open("config/compiler_config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default config if file doesn't exist
        default_config = {
            "compilers": {
                "python": {
                    "compile_cmd": "",  # Python doesn't need compilation
                    "run_cmd": "python {file}"
                },
                "c": {
                    "compile_cmd": "gcc {file} -o {output}",
                    "run_cmd": "{output}"
                },
                "cpp": {
                    "compile_cmd": "g++ {file} -o {output}",
                    "run_cmd": "{output}"
                },
                "java": {
                    "compile_cmd": "javac {file}",
                    "run_cmd": "java {classname}"
                }
            },
            "default_language": "python"
        }
        # Create config directory and file with default settings
        os.makedirs("config", exist_ok=True)
        with open("config/compiler_config.json", "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config

# Global variable to store config
CONFIG = load_config()

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Render the home page with the code editor."""
    languages = list(CONFIG["compilers"].keys())
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "languages": languages, "default_language": CONFIG["default_language"]}
    )

@app.post("/compile")
async def compile_code(code: str = Form(...), language: str = Form(...)):
    """Compile the provided code."""
    if language not in CONFIG["compilers"]:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
    
    compiler_config = CONFIG["compilers"][language]
    compile_cmd = compiler_config.get("compile_cmd")
    
    # If no compilation needed (like Python)
    if not compile_cmd:
        return {"success": True, "message": "No compilation needed for this language", "output": ""}
    
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(suffix=f".{language}", delete=False, mode="w") as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name
    
    output_path = temp_file_path + ".out"
    
    # Format the compile command
    formatted_cmd = compile_cmd.format(file=temp_file_path, output=output_path)
    
    try:
        # Run the compilation
        process = subprocess.run(
            formatted_cmd, 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if process.returncode != 0:
            return {
                "success": False, 
                "message": "Compilation failed", 
                "output": process.stderr or process.stdout
            }
        
        return {
            "success": True, 
            "message": "Compilation successful", 
            "output": process.stdout,
            "file_path": temp_file_path,
            "output_path": output_path
        }
    except Exception as e:
        return {"success": False, "message": f"Error during compilation: {str(e)}", "output": ""}
    finally:
        # Clean up is done in the run endpoint or after a timeout
        pass

@app.post("/run")
async def run_code(code: str = Form(...), language: str = Form(...), file_path: str = Form(None), output_path: str = Form(None), timeout: int = Form(30)):
    """Start running the compiled code or interpret the code directly."""
    global process_counter
    process_counter += 1
    execution_id = str(process_counter)
    
    if language not in CONFIG["compilers"]:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
    
    compiler_config = CONFIG["compilers"][language]
    run_cmd = compiler_config.get("run_cmd")
    
    if not run_cmd:
        return {"success": False, "message": "No run command configured for this language", "output": "", "execution_id": execution_id}
    
    # For interpreted languages or if file_path is not provided
    cleanup_temp_file = False
    if not file_path or not os.path.exists(file_path):
        with tempfile.NamedTemporaryFile(suffix=f".{language}", delete=False, mode="w") as temp_file:
            temp_file.write(code)
            file_path = temp_file.name
            cleanup_temp_file = True
    
    # Get class name for Java
    classname = ""
    if language == "java":
        # Extract class name from Java code
        import re
        match = re.search(r"public\s+class\s+(\w+)", code)
        if match:
            classname = match.group(1)
    
    # Format the run command
    formatted_cmd = run_cmd.format(
        file=file_path, 
        output=output_path or file_path + ".out",
        classname=classname
    )

    # Start the process in background
    def run_process():
        try:
            print(f"Running command: {formatted_cmd}")  # Debugging line
            
            # Start the process
            process = subprocess.Popen(
                formatted_cmd, 
                shell=True, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Update the process info
            if execution_id in active_processes:
                active_processes[execution_id]['process'] = process
            
            try:
                # Wait for process completion with timeout
                stdout, stderr = process.communicate(timeout=timeout)
                
                print(f"Process completed with return code: {process.returncode}")  # Debugging line
                
                # Update the process info with results
                if execution_id in active_processes:
                    active_processes[execution_id].update({
                        'completed': True,
                        'success': process.returncode == 0,
                        'output': stdout if process.returncode == 0 else stderr,
                        'exit_code': process.returncode,
                        'message': "Execution complete"
                    })
                
            except subprocess.TimeoutExpired:
                # Kill the process if it times out
                print(f"Process timed out after {timeout} seconds")
                try:
                    process.terminate()
                    try:
                        process.wait(timeout=2)  # Wait for graceful termination
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=1)  # Brief wait for kill
                except Exception as e:
                    print(f"Error terminating timed out process: {e}")
                
                # Update the process info with timeout
                if execution_id in active_processes:
                    active_processes[execution_id].update({
                        'completed': True,
                        'success': False,
                        'output': f"Process was terminated due to timeout ({timeout}s)",
                        'exit_code': -1,
                        'message': f"Execution timed out after {timeout} seconds"
                    })
                    
        except Exception as e:
            print(f"Error during execution: {str(e)}")
            # Update the process info with error
            if execution_id in active_processes:
                active_processes[execution_id].update({
                    'completed': True,
                    'success': False,
                    'output': str(e),
                    'exit_code': -1,
                    'message': f"Error during execution: {str(e)}"
                })
        finally:
            # Clean up temporary files
            try:
                if cleanup_temp_file and file_path and os.path.exists(file_path):
                    os.unlink(file_path)
                if output_path and os.path.exists(output_path):
                    os.unlink(output_path)
            except:
                pass
    
    # Initialize the process info
    active_processes[execution_id] = {
        'process': None,
        'start_time': time.time(),
        'cancelled': False,
        'completed': False,
        'timeout': timeout
    }
    
    # Start the process in a background thread
    thread = threading.Thread(target=run_process)
    thread.daemon = True
    thread.start()
    
    # Return immediately with execution ID
    return {
        "success": True,
        "message": "Execution started",
        "output": "",
        "execution_id": execution_id,
        "started": True
    }

@app.post("/cancel")
async def cancel_execution(execution_id: str = Form(...)):
    """Cancel a running execution."""
    print(f"Attempting to cancel execution with ID: {execution_id}")
    print(f"Active processes: {list(active_processes.keys())}")
    
    if execution_id not in active_processes:
        return {"success": False, "message": "Execution not found or already completed"}
    
    try:
        process_info = active_processes[execution_id]
        process = process_info.get('process')
        print(f"Process to cancel: {process}")
        
        # Mark as cancelled
        process_info['cancelled'] = True
        
        # Update status to cancelled
        process_info.update({
            'completed': True,
            'success': False,
            'output': "Execution was cancelled by user",
            'exit_code': -2,
            'message': "Execution cancelled"
        })
        
        # Terminate the process if it exists and is running
        if process and process.poll() is None:  # Process is still running
            print(f"Terminating process")
            try:
                # First try to terminate gracefully
                process.terminate()
                print(f"Process terminated, waiting...")
                
                # Wait a short time for graceful termination
                try:
                    process.wait(timeout=2)
                    print(f"Process terminated gracefully")
                except subprocess.TimeoutExpired:
                    # If graceful termination fails, force kill
                    print(f"Force killing process")
                    process.kill()
                    # Don't call communicate() here as it can hang
                    process.wait(timeout=1)  # Brief wait for kill to complete
                    print(f"Process force killed")
            except Exception as kill_error:
                print(f"Error killing process: {kill_error}")
        else:
            print(f"Process already terminated or None")
        
        return {
            "success": True, 
            "message": "Execution cancelled successfully",
            "execution_id": execution_id,
            "cancelled": True
        }
    except Exception as e:
        print(f"Error cancelling execution: {str(e)}")
        return {"success": False, "message": f"Error cancelling execution: {str(e)}"}

@app.get("/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get the status of a running execution."""
    if execution_id not in active_processes:
        return {"running": False, "message": "Execution not found or completed"}
    
    process_info = active_processes[execution_id]
    elapsed_time = time.time() - process_info['start_time']
    
    # Check if execution completed
    if process_info.get('completed', False):
        # Remove from active processes and return final results
        final_result = {
            "running": False,
            "completed": True,
            "success": process_info.get('success', False),
            "message": process_info.get('message', 'Execution completed'),
            "output": process_info.get('output', ''),
            "exit_code": process_info.get('exit_code'),
            "elapsed_time": round(elapsed_time, 2),
            "cancelled": process_info.get('cancelled', False)
        }
        
        # Clean up
        del active_processes[execution_id]
        return final_result
    
    return {
        "running": True,
        "completed": False,
        "elapsed_time": round(elapsed_time, 2),
        "timeout": process_info.get('timeout', 30),
        "cancelled": process_info.get('cancelled', False)
    }

@app.get("/config")
async def get_config():
    """Return the current compiler configuration."""
    return CONFIG

@app.post("/config")
async def update_config(config: Dict[str, Any]):
    """Update the compiler configuration."""
    global CONFIG
    
    # Validate config structure
    if "compilers" not in config or not isinstance(config["compilers"], dict):
        raise HTTPException(status_code=400, detail="Invalid config: missing 'compilers' object")
    
    if "default_language" not in config or config["default_language"] not in config["compilers"]:
        raise HTTPException(status_code=400, detail="Invalid config: missing or invalid 'default_language'")
    
    # Update config
    CONFIG = config
    
    # Save to file
    with open("config/compiler_config.json", "w") as f:
        json.dump(CONFIG, f, indent=4)
    
    return {"success": True, "message": "Configuration updated successfully"}

@app.get("/examples")
async def get_examples():
    """Return the list of available examples."""
    try:
        with open("examples/examples_index.json", "r") as f:
            examples = json.load(f)
        return examples
    except FileNotFoundError:
        return {"error": "Examples index not found"}
    except Exception as e:
        return {"error": f"Failed to load examples: {str(e)}"}

@app.get("/examples/{language}/{filename}")
async def get_example_code(language: str, filename: str):
    """Return the code for a specific example."""
    try:
        # Validate language
        if language not in CONFIG["compilers"]:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
        
        # Construct file path
        file_path = f"examples/{filename}"
        
        # Security check: ensure file is in examples directory
        if not os.path.abspath(file_path).startswith(os.path.abspath("examples")):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Read the file
        with open(file_path, "r") as f:
            code = f.read()
        
        return {"code": code, "filename": filename, "language": language}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Example file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load example: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
