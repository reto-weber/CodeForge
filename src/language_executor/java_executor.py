import re
from typing import Optional, Tuple, List, Union

from container_manager import get_container_manager

from .base import LanguageExecutor, FileInfo


class JavaExecutor(LanguageExecutor):
    def compile(
        self, 
        code: Union[str, List[FileInfo]], 
        session_id: str, 
        main_file: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        print(f"Compiling Java code in session {session_id}")
        container_mgr = get_container_manager()
        
        if not container_mgr.create_session_container(session_id, "java"):
            return False, "Failed to create compilation container", None
            
        # Normalize input to handle both single and multi-file scenarios
        files, main_filename = self._normalize_input(code, main_file)
        
        # Write all files to container
        if not self._write_files_to_container(files, session_id):
            return False, "Failed to copy files to container", None
            
        # Find the main class from the main file
        main_file_content = None
        for file_info in files:
            if file_info.name == main_filename:
                main_file_content = file_info.content
                break
                
        if not main_file_content:
            return False, f"Main file '{main_filename}' not found", None
            
        # Extract class name from main file
        match = re.search(r"public\s+class\s+(\w+)", main_file_content)
        if match:
            class_name = match.group(1)
            expected_filename = f"{class_name}.java"
            
            # Rename main file if needed
            if main_filename != expected_filename:
                container_mgr.run_command_in_container(
                    session_id, f"mv {main_filename} {expected_filename}", 5
                )
                main_filename = expected_filename
        else:
            class_name = "Main"  # Default class name
            
        # Compile all Java files (*.java)
        compile_cmd = "javac *.java"
        exec_result = container_mgr.run_command_in_container(session_id, compile_cmd, 30)
        
        if exec_result is None:
            return False, "Failed to compile code in container", None
            
        stdout = exec_result.output[0].decode("utf-8") if exec_result.output[0] else ""
        stderr = exec_result.output[1].decode("utf-8") if exec_result.output[1] else ""
        exit_code = exec_result.exit_code
        output = stdout if exit_code == 0 else (stderr or stdout)
        success = exit_code == 0
        
        # Return class name for execution
        output_path = class_name if success else None
        return success, output, output_path

    def execute(
        self, 
        code: Union[str, List[FileInfo]], 
        session_id: str, 
        timeout: int = 30,
        main_file: Optional[str] = None
    ) -> Tuple[bool, str, int]:
        print(f"Executing Java code in session {session_id}")
        container_mgr = get_container_manager()
        
        # Normalize input to handle both single and multi-file scenarios
        files, main_filename = self._normalize_input(code, main_file)
        
        # Find the main file content to extract class name
        main_file_content = None
        for file_info in files:
            if file_info.name == main_filename:
                main_file_content = file_info.content
                break
                
        if not main_file_content:
            return False, f"Main file '{main_filename}' not found", -1
            
        # Extract class name from main file
        match = re.search(r"public\s+class\s+(\w+)", main_file_content)
        if match:
            class_name = match.group(1)
        else:
            class_name = "Main"  # Default class name
            
        run_cmd = f"java {class_name}"
        run_result = container_mgr.run_command_in_container(
            session_id, run_cmd, timeout
        )
        
        if run_result is None:
            return False, "Failed to execute class in container", -1
            
        stdout = run_result.output[0].decode("utf-8") if run_result.output[0] else ""
        stderr = run_result.output[1].decode("utf-8") if run_result.output[1] else ""
        exit_code = run_result.exit_code
        output = stdout if exit_code == 0 else (stderr or stdout)
        success = exit_code == 0
        
        return success, output, exit_code
