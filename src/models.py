from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    name: str = Field(..., description="Filename with extension")
    content: str = Field(..., description="File content")


class CompileRequest(BaseModel):
    code: str = Field(..., description="Source code to compile")
    language: str = Field(..., description="Programming language")


class MultiFileRequest(BaseModel):
    language: str = Field(..., description="Programming language")
    files: List[FileInfo] = Field(..., description="List of files")
    main_file: str = Field(..., description="Main file to execute")
    timeout: Optional[int] = Field(30, description="Execution timeout in seconds")
    file_path: Optional[str] = Field(None, description="Pre-compiled file path")
    output_path: Optional[str] = Field(None, description="Pre-compiled output path")


class CompileResponse(BaseModel):
    success: bool = Field(..., description="Whether compilation succeeded")
    message: str = Field(..., description="Compilation status message")
    output: str = Field(..., description="Compiler output")
    file_path: Optional[str] = Field(None, description="Path to source file")
    output_path: Optional[str] = Field(None, description="Path to compiled output")


class RunRequest(BaseModel):
    code: str = Field(..., description="Source code to execute")
    language: str = Field(..., description="Programming language")
    timeout: int = Field(30, description="Execution timeout in seconds")
    file_path: Optional[str] = Field(None, description="Pre-compiled file path")
    output_path: Optional[str] = Field(None, description="Pre-compiled output path")


class RunResponse(BaseModel):
    success: bool = Field(..., description="Whether execution started successfully")
    message: str = Field(..., description="Execution status message")
    started: bool = Field(..., description="Whether execution process started")
    execution_id: Optional[str] = Field(None, description="Unique execution ID")
    output: Optional[str] = Field(None, description="Execution output (if immediate)")


class StatusResponse(BaseModel):
    running: bool = Field(..., description="Whether execution is still running")
    completed: bool = Field(..., description="Whether execution completed")
    success: bool = Field(..., description="Whether execution was successful")
    message: str = Field(..., description="Status message")
    output: Optional[str] = Field(None, description="Execution output")
    exit_code: Optional[int] = Field(None, description="Process exit code")
    elapsed_time: float = Field(..., description="Elapsed time in seconds")


class SessionInfo(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    session_created: float = Field(..., description="Session creation timestamp")
    session_last_used: float = Field(..., description="Last activity timestamp")
    container: Optional[Dict[str, Any]] = Field(None, description="Container info")


class ExampleInfo(BaseModel):
    title: str = Field(..., description="Example title")
    description: str = Field(..., description="Example description")
    code: str = Field(..., description="Example source code")


class UserSession(BaseModel):
    created_at: float
    last_used: float


class ActiveProcess(BaseModel):
    session_id: str
    start_time: float
    cancelled: bool = False
    completed: bool = False
    timeout: int = 30
    language: str
    operation_type: str = "run"  # "run", "compile", or "verify"
    success: Optional[bool] = None
    output: Optional[str] = None
    exit_code: Optional[int] = None
    message: Optional[str] = None


class CompilerConfig(BaseModel):
    compilers: List[str] = Field(..., description="Names of programming languages")
    default_language: str = Field(..., description="Default language for the editor")
