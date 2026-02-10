"""
Process Executor Service
Executes Python code in a separate process with resource limits
"""

import sys
import os
import json
import uuid
import time
import shutil
import tempfile
import subprocess
import traceback
from typing import Any, Dict, Optional, Tuple
import pandas as pd
import numpy as np

from app.config import settings


class ProcessExecutor:
    """
    Execute Python code in a separate process.

    WARNING: This executor runs code on the host machine in a subprocess.
    It provides process isolation but NOT full system isolation (filesystem, network).
    This implementation is intended for development environments where Docker
    is not available. In production, use a container-based executor (Docker, E2B, etc.).
    """

    def __init__(self):
        self.python_executable = sys.executable

    def validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate code for security issues.
        Process execution is safer than exec(), but we still want basic checks.
        """
        # We can reuse the AST-based validation from CodeExecutor if needed,
        # but since we run in a separate process, we are protected from crash/exit calls affecting the main app.
        # However, we should still block dangerous imports like 'os', 'subprocess' etc.
        # to prevent system access.

        # Simple string check for now
        dangerous_terms = ['os.system', 'subprocess.', 'shutil.', 'sys.exit']
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
        Execute Python code in a separate process.

        Args:
            code: Python code to execute
            dataframe: Optional dataframe to make available as 'df'
            timeout: Execution timeout in seconds

        Returns:
            Dictionary with execution results
        """
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="beagle_exec_")

        try:
            # Prepare data file if needed
            data_file = None
            if dataframe is not None:
                data_file = os.path.join(temp_dir, "data.parquet")
                dataframe.to_parquet(data_file)

            # Prepare script
            script_file = os.path.join(temp_dir, "script.py")
            wrapped_code = self._wrap_code(code, data_file)

            with open(script_file, "w") as f:
                f.write(wrapped_code)

            # Execute
            start_time = time.time()

            try:
                # Run process with limits
                process = subprocess.run(
                    [self.python_executable, script_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=temp_dir,
                    env=self._get_restricted_env()
                )

                execution_time = int((time.time() - start_time) * 1000)

                # Check exit code
                if process.returncode != 0:
                    return {
                        "success": False,
                        "error": process.stderr,
                        "stdout": process.stdout,
                        "stderr": process.stderr,
                        "result": None,
                        "execution_time_ms": execution_time,
                        "visualizations": None
                    }

                # Parse output
                # The script prints the JSON result to a specific file or as the last line of stdout
                # Here we used a specific file 'result.json' in the wrapper
                result_file = os.path.join(temp_dir, "result.json")
                if os.path.exists(result_file):
                    with open(result_file, "r") as f:
                        execution_result = json.load(f)

                    return {
                        "success": True,
                        "result": execution_result.get("variables", {}),
                        "stdout": process.stdout,
                        "stderr": process.stderr,
                        "execution_time_ms": execution_time,
                        "visualizations": execution_result.get("visualizations")
                    }
                else:
                    return {
                        "success": True,  # Process finished but no result file? Maybe empty script
                        "result": {},
                        "stdout": process.stdout,
                        "stderr": process.stderr,
                        "execution_time_ms": execution_time,
                        "visualizations": None
                    }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"Execution timed out after {timeout} seconds",
                    "stdout": "",  # Can't easily capture output on timeout with run()
                    "stderr": "TimeoutExpired",
                    "result": None,
                    "execution_time_ms": timeout * 1000,
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
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _wrap_code(self, user_code: str, data_file: Optional[str]) -> str:
        """Wrap user code with setup and teardown logic"""
        from app.services.code_wrapper import wrap_code
        return wrap_code(user_code, data_file)

    def _get_restricted_env(self) -> Dict[str, str]:
        """Get environment variables for the subprocess"""
        # strict allowlist to prevent secret leakage
        allowed_keys = {
            'PATH', 'LANG', 'LC_ALL', 'HOME', 'USER',
            'TZ', 'PYTHONPATH', 'LD_LIBRARY_PATH', 'LIBRARY_PATH'
        }

        env = {k: v for k, v in os.environ.items() if k in allowed_keys}

        # Add restriction flags
        env['PYTHONHASHSEED'] = '0'
        # Prevent writing bytecode
        env['PYTHONDONTWRITEBYTECODE'] = '1'

        return env
