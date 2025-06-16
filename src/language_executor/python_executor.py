from typing import Optional, Tuple, Union, List

from container_manager import get_container_manager

from .base import LanguageExecutor, FileInfo


class PythonExecutor(LanguageExecutor):
    def compile(
        self, 
        code: Union[str, List[FileInfo]], 
        session_id: str, 
        main_file: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        # Python does not need compilation, but we may need to write files
        if isinstance(code, list):
            container_mgr = get_container_manager()
            if not container_mgr.create_session_container(session_id, "python"):
                return False, "Failed to create container", None
            if not self._write_files_to_container(code, session_id):
                return False, "Failed to copy files to container", None
        return True, "No compilation needed for Python", None

    def execute(
        self, 
        code: Union[str, List[FileInfo]], 
        session_id: str, 
        timeout: int = 30,
        main_file: Optional[str] = None
    ) -> Tuple[bool, str, int]:
        container_mgr = get_container_manager()
        
        # Ensure container exists
        if not container_mgr.create_session_container(session_id, "python"):
            return False, "Failed to create execution container", -1

        if isinstance(code, list):
            # Multi-file execution
            if not self._write_files_to_container(code, session_id):
                return False, "Failed to copy files to container", -1
            
            # Use main_file if specified, otherwise find a .py file
            if main_file:
                filename = main_file
            else:
                py_files = [f.name for f in code if f.name.endswith('.py')]
                if not py_files:
                    return False, "No Python files found", -1
                filename = py_files[0]
        else:
            # Legacy single file execution
            filename = "code.py"
            if not container_mgr.put_file_in_container(session_id, filename, code):
                return False, "Failed to copy code to container", -1

        # Run command
        cmd = f"python3 {filename}"
        exec_result = container_mgr.run_command_in_container(session_id, cmd, timeout)
        if exec_result is None:
            return False, "Failed to execute command in container", -1
            
        stdout = exec_result.output[0].decode("utf-8") if exec_result.output[0] else ""
        stderr = exec_result.output[1].decode("utf-8") if exec_result.output[1] else ""
        exit_code = exec_result.exit_code
        output = stdout if exit_code == 0 else (stderr or stdout)
        success = exit_code == 0
        return success, output, exit_code
