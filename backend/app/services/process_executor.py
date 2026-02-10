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

        setup_code = """
import sys
import json
import os
import pandas as pd
import numpy as np
import scipy.stats
import sklearn
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# Configure matplotlib to not use X server
plt.switch_backend('Agg')

# Load data
df = None
"""

        if data_file:
            setup_code += """
try:
    df = pd.read_parquet('data.parquet')
except Exception as e:
    print(f"Error loading data: {e}", file=sys.stderr)
"""

        teardown_code = """
# --- User Code Ends ---

# Serialization Logic
def safe_serialize(obj):
    if isinstance(obj, (pd.DataFrame, pd.Series)):
        # Return metadata for large objects
        if isinstance(obj, pd.DataFrame):
            return {
                "type": "dataframe",
                "shape": obj.shape,
                "columns": obj.columns.tolist(),
                "preview": obj.head(10).to_dict(orient='records')
            }
        else:
            return {
                "type": "series",
                "length": len(obj),
                "preview": obj.head(10).to_dict()
            }
    elif isinstance(obj, np.ndarray):
        return {
            "type": "array",
            "shape": obj.shape,
            "preview": obj.flatten()[:20].tolist()
        }
    elif isinstance(obj, (int, float, str, bool, list, dict, tuple)):
        try:
            json.dumps(obj)
            return obj
        except:
            return str(obj)
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    else:
        return str(obj)

# Collect variables
variables = {}
# We filter for user-defined variables (not starting with _)
# and exclude modules
import types
for name, val in list(locals().items()):
    if name.startswith('_') or name in ['sys', 'json', 'os', 'pd', 'np', 'scipy', 'sklearn', 'sm', 'plt', 'sns', 'px', 'go', 'pio', 'safe_serialize', 'variables']:
        continue
    if isinstance(val, types.ModuleType):
        continue
    if name == 'df' and isinstance(val, pd.DataFrame):
        # Only include df if it was modified or is relevant?
        # For now, always include if present
        pass

    variables[name] = safe_serialize(val)

# Collect visualizations
# (This is tricky without display hooks, but we can check if any figures were created)
visualizations = []
# Check matplotlib figures
if plt.get_fignums():
    # Save to base64 or similar?
    # For now, we just note that plots were created.
    # To really support this, we'd need to hook into plt.show()
    pass

# Check plotly figures
# If user assigned a figure to a variable, we might have caught it in 'variables'
# But if they just called fig.show(), it's gone.
# We can overwrite fig.show() in the setup code to capture it.

output = {
    "variables": variables,
    "visualizations": visualizations
}

with open("result.json", "w") as f:
    json.dump(output, f, default=str)
"""

        return setup_code + "\n" + user_code + "\n" + teardown_code

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
