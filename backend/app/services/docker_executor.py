"""
Docker Executor Service
Executes Python code in an isolated Docker container
"""

import os
import json
import time
import shutil
import tempfile
import traceback
from typing import Any, Dict, Optional, Tuple
import pandas as pd
import docker
from docker.errors import DockerException, APIError, ContainerError

from app.config import settings
from app.services.code_wrapper import wrap_code


class DockerExecutor:
    """
    Execute Python code in an isolated Docker container.

    This executor runs code inside a container with limited resources and no network access.
    It provides strong isolation for security.
    """

    def __init__(self):
        try:
            self.client = docker.from_env()
        except DockerException:
            self.client = None

        self.image = "beagle-sandbox"

    def validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate code for basic security issues.
        Even with Docker, we should avoid running obviously malicious scripts.
        """
        # Block subprocess/os calls that might try to exploit container escape (though rare)
        dangerous_terms = ['os.system', 'subprocess.']
        for term in dangerous_terms:
            if term in code:
                return False, f"Blocked term detected: {term}"

        return True, None

    async def execute(
        self,
        code: str,
        dataframe: Optional[pd.DataFrame] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute Python code in a Docker container.

        Args:
            code: Python code to execute
            dataframe: Optional dataframe to make available as 'df'
            timeout: Execution timeout in seconds

        Returns:
            Dictionary with execution results
        """
        if not self.client:
             return {
                "success": False,
                "error": "Docker client not initialized. Is Docker running?",
                "result": None,
                "execution_time_ms": 0,
                "visualizations": None
            }

        # Create temporary directory on host
        temp_dir = tempfile.mkdtemp(prefix="beagle_docker_")

        try:
            # Prepare data file if needed
            data_file = None
            if dataframe is not None:
                # We save it as 'data.parquet' in the temp dir
                dataframe.to_parquet(os.path.join(temp_dir, "data.parquet"))
                data_file = "/app/data.parquet" # Path inside container

            # Prepare script
            wrapped_code = wrap_code(code, data_file)

            with open(os.path.join(temp_dir, "script.py"), "w") as f:
                f.write(wrapped_code)

            # Configure execution
            start_time = time.time()
            container = None

            try:
                # Run container
                # We mount the temp dir to /app in the container
                # We set strict limits
                container = self.client.containers.run(
                    image=self.image,
                    command="python3 script.py",
                    volumes={
                        temp_dir: {'bind': '/app', 'mode': 'rw'}
                    },
                    working_dir="/app",
                    network_mode="none",  # No network access
                    mem_limit="512m",     # 512MB RAM limit
                    cpu_period=100000,
                    cpu_quota=50000,      # 0.5 CPU limit
                    detach=True,
                    user="sandbox",       # Run as non-root user
                    # Security options
                    cap_drop=['ALL'],
                    security_opt=['no-new-privileges']
                )

                # Wait for result with timeout
                try:
                    result = container.wait(timeout=timeout)
                    exit_code = result.get('StatusCode', 1)
                except Exception as e:
                    # Timeout handling
                    container.kill()
                    raise TimeoutError(f"Execution timed out after {timeout} seconds")

                execution_time = int((time.time() - start_time) * 1000)

                # Get logs
                stdout_bytes = container.logs(stdout=True, stderr=False)
                stderr_bytes = container.logs(stdout=False, stderr=True)

                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')

                # Check exit code
                if exit_code != 0:
                    return {
                        "success": False,
                        "error": stderr or "Unknown error",
                        "stdout": stdout,
                        "stderr": stderr,
                        "result": None,
                        "execution_time_ms": execution_time,
                        "visualizations": None
                    }

                # Parse output file (written by script.py inside container to shared volume)
                result_file = os.path.join(temp_dir, "result.json")
                if os.path.exists(result_file):
                    with open(result_file, "r") as f:
                        execution_result = json.load(f)

                    return {
                        "success": True,
                        "result": execution_result.get("variables", {}),
                        "stdout": stdout,
                        "stderr": stderr,
                        "execution_time_ms": execution_time,
                        "visualizations": execution_result.get("visualizations")
                    }
                else:
                     return {
                        "success": True,
                        "result": {},
                        "stdout": stdout,
                        "stderr": stderr,
                        "execution_time_ms": execution_time,
                        "visualizations": None
                    }

            except TimeoutError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "stdout": "",
                    "stderr": "TimeoutExpired",
                    "result": None,
                    "execution_time_ms": timeout * 1000,
                    "visualizations": None
                }

            except (APIError, ContainerError) as e:
                return {
                    "success": False,
                    "error": f"Docker error: {str(e)}",
                    "stdout": "",
                    "stderr": traceback.format_exc(),
                    "result": None,
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "visualizations": None
                }
            except Exception as e:
                 return {
                    "success": False,
                    "error": str(e),
                    "stdout": "",
                    "stderr": traceback.format_exc(),
                    "result": None,
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "visualizations": None
                }
            finally:
                # Remove container
                if container:
                    try:
                        container.remove(force=True)
                    except:
                        pass

        finally:
            # Cleanup temp dir
            shutil.rmtree(temp_dir, ignore_errors=True)
