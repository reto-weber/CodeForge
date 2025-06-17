"""
Docker Container Manager for Code Execution

This module handles Docker container lifecycle for secure code execution.
Each user session gets a dedicated container for isolation.
"""

import io
import logging
import signal
import tarfile
import threading
import time
from pathlib import Path
from typing import Dict, Optional

import docker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContainerManager:
    """Manages Docker containers for code execution."""

    _instance = None
    _initialized = False

    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(ContainerManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the Docker client (only once)."""
        # Prevent re-initialization of already initialized instance
        if self._initialized:
            return

        try:
            self.client: docker.DockerClient

            # Try Linux/WSL Docker connection methods
            # Method 1: Try from environment (default Linux socket)
            try:
                self.client = docker.from_env()
                self.client.ping()
                logger.info("Docker client initialized from environment")
            except docker.errors.DockerException as env_e:
                logger.debug("Failed to initialize from env: %s", env_e)

                # Method 2: Try Unix socket directly
                try:
                    self.client = docker.DockerClient(
                        base_url="unix://var/run/docker.sock"
                    )
                    self.client.ping()
                    logger.info("Docker client initialized via Unix socket")
                except docker.errors.DockerException as socket_e:
                    logger.debug("Failed via Unix socket: %s", socket_e)

                    # Method 3: Try TCP for Docker-in-Docker scenarios
                    try:
                        self.client = docker.DockerClient(
                            base_url="tcp://localhost:2376"
                        )
                        self.client.ping()
                        logger.info("Docker client initialized via TCP")
                    except docker.errors.DockerException as tcp_e:
                        logger.debug("Failed via TCP: %s", tcp_e)

                        # All methods failed
                        raise docker.errors.DockerException(
                            f"All Docker connection methods failed. "
                            f"env={env_e}, socket={socket_e}, tcp={tcp_e}"
                        ) from tcp_e

            if self.client is None:
                raise RuntimeError("Failed to initialize Docker client")

        except Exception as e:
            logger.error("Failed to initialize Docker client: %s", e)
            raise RuntimeError(f"Docker is not available: {e}") from e

        self.active_containers: Dict[str, dict] = {}
        # Language-specific Docker images
        self.language_images = {
            "python": "code-executor-python:latest",
            "c": "code-executor-c:latest",
            "cpp": "code-executor-cpp:latest",
            "java": "code-executor-java:latest",
            "eiffel": "code-executor-eiffel:latest",
        }
        # Fallback image name for backward compatibility
        self.image_name = "code-executor:latest"

        # Clean up any existing containers on startup
        logger.info("Cleaning up existing code execution containers on startup...")
        cleanup_count = self.cleanup_all_code_containers()
        if cleanup_count > 0:
            logger.info("Cleaned up %d existing containers", cleanup_count)

        # Set up shutdown handlers
        self._setup_shutdown_handler()

        # Mark as initialized to prevent re-initialization
        self._initialized = True

    def build_execution_image(self) -> bool:
        """Build the Docker image for code execution."""
        try:
            dockerfile_path = (
                Path(__file__).parent.parent / "docker" / "Dockerfile.execution"
            )
            if not dockerfile_path.exists():
                logger.error("Dockerfile.execution not found")
                return False

            logger.info("Building execution Docker image...")
            docker_dir = Path(__file__).parent.parent / "docker"
            self.client.images.build(
                path=str(docker_dir),
                dockerfile="Dockerfile.execution",
                tag=self.image_name,
                rm=True,
                forcerm=True,
            )
            logger.info("Docker image built successfully")
            return True
        except docker.errors.DockerException as e:
            logger.error("Failed to build Docker image: %s", e)
            return False

    def get_image_for_language(self, language: str) -> str:
        """Get the appropriate Docker image for a language."""
        return self.language_images.get(language, self.image_name)

    def ensure_image_exists(self, language: str) -> bool:
        """Ensure the execution image exists, build if necessary."""
        try:
            image_name = (
                self.get_image_for_language(language) if language else self.image_name
            )
            self.client.images.get(image_name)
            logger.info("Execution image %s already exists", image_name)
            return True
        except docker.errors.ImageNotFound:
            logger.info("Execution image %s not found", image_name)
            if language:
                logger.error(
                    "Language-specific image %s not found. Please build it first.",
                    image_name,
                )
                return False
            else:
                logger.info("Building fallback image...")
                return self.build_execution_image()
        except docker.errors.DockerException as e:
            logger.error("Error checking image: %s", e)
            return False

    def create_session_container(
        self, session_id: str, language: str = "python"
    ) -> Optional[str]:
        """Create a new container for a user session."""
        try:
            image_name = self.get_image_for_language(language)
            if not self.ensure_image_exists(language):
                return None

            container_name = f"code-session-{session_id}"

            # Remove existing container if it exists
            self.cleanup_session_container(session_id)

            container = self.client.containers.run(
                image_name,
                name=container_name,
                detach=True,
                remove=False,  # We'll remove manually for cleanup control
                working_dir="/workspace",
                # mem_limit="512m",  # Memory limit for security
                # cpu_quota=50000,  # CPU limit (50% of one core)
                network_disabled=True,  # Disable network for security
                user="coderunner",
                command="sleep infinity",  # Keep container running
            )

            self.active_containers[session_id] = {
                "container": container,
                "container_id": container.id,
                "created_at": time.time(),
                "name": container_name,
            }

            logger.info(
                "Created container %s for session %s", container_name, session_id
            )
            return container.id

        except docker.errors.DockerException as e:
            logger.error("Failed to create container for session %s: %s", session_id, e)
            return None

    def _execute_with_timeout(self, container, cmd: str, timeout: int):
        """Execute command with timeout using container.exec_run."""
        # Execute the command
        logger.info("Executing command in container %s: %s", container, cmd)
        exec_result = container.exec_run(
            f"sh -c '{cmd}'",
            stdout=True,
            stderr=True,
            stream=False,
            demux=True,
            user="coderunner",  # Run as coderunner user, not root
        )
        return exec_result

    def cancel_execution(self, session_id: str) -> bool:
        """Cancel running execution in the session container."""
        try:
            if session_id not in self.active_containers:
                return False

            container = self.active_containers[session_id]["container"]

            # Kill all processes in the container (Alpine compatible)
            try:
                container.exec_run(
                    "pkill -f 'python3|gcc|g++|java|javac' || true",
                    user="coderunner",  # Run as coderunner user, not root
                )
                logger.info("Cancelled execution for session %s", session_id)
                return True
            except Exception as e:
                logger.error(
                    "Error cancelling execution for session %s: %s", session_id, e
                )
                return False

        except Exception as e:
            logger.error("Error cancelling execution for session %s: %s", session_id, e)
            return False

    def cleanup_session_container(self, session_id: str) -> bool:
        """Clean up the container for a session."""
        try:
            if session_id in self.active_containers:
                container_info = self.active_containers[session_id]
                container = container_info["container"]

                try:
                    container.stop(timeout=5)
                    container.remove()
                    logger.info("Cleaned up container for session %s", session_id)
                except Exception as e:
                    logger.warning(
                        "Error stopping/removing container for session %s: %s",
                        session_id,
                        e,
                    )

                del self.active_containers[session_id]
                return True
            else:
                # Try to find and remove container by name
                container_name = f"code-session-{session_id}"
                try:
                    container = self.client.containers.get(container_name)
                    container.stop(timeout=5)
                    container.remove()
                    logger.info("Cleaned up orphaned container %s", container_name)
                except docker.errors.NotFound:
                    pass  # Container doesn't exist, which is fine
                except Exception as e:
                    logger.warning(
                        "Error cleaning up orphaned container %s: %s", container_name, e
                    )

                return True

        except Exception as e:
            logger.error(
                "Error cleaning up container for session %s: %s", session_id, e
            )
            return False

    def cleanup_old_containers(self, max_age_hours: int = 24) -> int:
        """Clean up containers older than specified hours."""
        cleaned_count = 0
        current_time = time.time()

        sessions_to_cleanup = []
        for session_id, container_info in self.active_containers.items():
            age_hours = (current_time - container_info["created_at"]) / 3600
            if age_hours > max_age_hours:
                sessions_to_cleanup.append(session_id)

        for session_id in sessions_to_cleanup:
            if self.cleanup_session_container(session_id):
                cleaned_count += 1

        logger.info("Cleaned up %s old containers", cleaned_count)
        return cleaned_count

    def get_session_info(self, session_id: str) -> Optional[dict]:
        """Get information about a session container."""
        if session_id not in self.active_containers:
            return None

        container_info = self.active_containers[session_id]
        try:
            container = container_info["container"]
            container.reload()

            return {
                "session_id": session_id,
                "container_id": container_info["container_id"],
                "status": container.status,
                "created_at": container_info["created_at"],
                "age_seconds": time.time() - container_info["created_at"],
            }
        except Exception as e:
            logger.error("Error getting session info for %s: %s", session_id, e)

    def _create_tar_archive(self, filename: str, content: str) -> bytes:
        """Create a tar archive containing the file with given content."""

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            file_data = content.encode("utf-8")
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(file_data)
            tarinfo.mode = 0o644
            # Set ownership to coderunner user (UID 1000, GID 1000)
            tarinfo.uid = 1000
            tarinfo.gid = 1000
            tarinfo.uname = "coderunner"
            tarinfo.gname = "coderunner"
            tar.addfile(tarinfo, io.BytesIO(file_data))

        tar_buffer.seek(0)
        return tar_buffer.getvalue()

    def put_file_in_container(self, session_id: str, filename: str, code: str) -> bool:
        """
        Copy a file with the given code into the session's container at
        /workspace/filename.
        """
        if session_id not in self.active_containers:
            return False
        container = self.active_containers[session_id]["container"]
        try:
            container.put_archive(
                "/workspace", self._create_tar_archive(filename, code)
            )

            # Update file metadata to ensure proper ownership and timestamps
            touch_result = container.exec_run(
                f"touch {filename}", user="coderunner", workdir="/workspace"
            )

            if touch_result.exit_code != 0:
                logger.warning(
                    "Failed to update file metadata for %s in session %s",
                    filename,
                    session_id,
                )

            return True
        except Exception as e:
            logger.error(
                "Failed to put file in container for session %s: %s", session_id, e
            )
            return False

    def run_command_in_container(self, session_id: str, cmd: str, timeout: int = 30):
        """
        Run a shell command in the session's container and return the exec
        result object (with .exit_code, .output).
        """
        if session_id not in self.active_containers:
            return None
        container = self.active_containers[session_id]["container"]
        try:
            return self._execute_with_timeout(container, cmd, timeout)
        except Exception as e:
            logger.error(
                "Failed to run command in container for session %s: %s", session_id, e
            )
            return None

    def read_file_from_container(
        self, session_id: str, filename: str, encoding: str = "utf-8"
    ) -> str:
        """Read the content of a file from the container for the given session."""
        if session_id not in self.active_containers:
            raise RuntimeError(f"No active container for session {session_id}")
        container = self.active_containers[session_id]["container"]
        # Use 'cat' to read the file content
        exec_result = container.exec_run(
            f"cat {filename}",
            stdout=True,
            stderr=True,
            stream=False,
            demux=True,
            user="coderunner",
        )
        if exec_result.exit_code != 0:
            stderr = (
                exec_result.output[1].decode(encoding) if exec_result.output[1] else ""
            )
            raise RuntimeError(
                f"Failed to read file {filename} from container: {stderr}"
            )
        stdout = exec_result.output[0].decode(encoding) if exec_result.output[0] else ""
        return stdout

    def cleanup_all_code_containers(self) -> int:
        """Clean up all code execution containers (startup/shutdown cleanup)."""
        cleaned_count = 0

        try:
            # Get all containers with our naming pattern
            all_containers = self.client.containers.list(all=True)

            for container in all_containers:
                container_name = container.name

                # Check if this is one of our code execution containers
                if container_name.startswith("code-session-"):
                    try:
                        logger.info("Cleaning up container: %s", container_name)

                        # Stop container if running
                        if container.status == "running":
                            container.stop(timeout=5)

                        # Remove container
                        container.remove()
                        cleaned_count += 1

                    except Exception as e:
                        logger.warning(
                            "Error cleaning up container %s: %s",
                            container_name,
                            e,
                        )

            # Clear our active containers tracking
            self.active_containers.clear()

            logger.info("Cleaned up %s code execution containers", cleaned_count)
            return cleaned_count

        except Exception as e:
            logger.error("Error during container cleanup: %s", e)
            return cleaned_count

    def _setup_shutdown_handler(self):
        """Set up signal handlers for graceful shutdown."""
        # Only set up signal handlers in the main thread
        if threading.current_thread() is not threading.main_thread():
            logger.debug("Skipping signal handler setup (not in main thread)")
            return

        def shutdown_handler(signum, frame):
            logger.info("Received signal %s, cleaning up containers...", signum)
            self.cleanup_all_code_containers()
            logger.info("Container cleanup completed")
            # Let the default handler continue
            signal.default_int_handler(signum, frame)

        try:
            # Register signal handlers
            signal.signal(signal.SIGINT, shutdown_handler)
            signal.signal(signal.SIGTERM, shutdown_handler)
            logger.debug("Signal handlers set up successfully")
        except ValueError as e:
            # This can happen in some testing environments
            logger.debug("Could not set up signal handlers: %s", e)


# Global container manager instance
CONTAINER_MANAGER = None


def get_container_manager() -> ContainerManager:
    """Get the global container manager instance."""
    global CONTAINER_MANAGER
    if CONTAINER_MANAGER is None:
        CONTAINER_MANAGER = ContainerManager()
    return CONTAINER_MANAGER
