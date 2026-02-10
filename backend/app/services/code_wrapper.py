"""
Code Wrapper Logic
Helper to wrap user code for execution and result capture
"""

from typing import Optional

def wrap_code(user_code: str, data_file: Optional[str] = None) -> str:
    """
    Wrap user code with setup and teardown logic to capture results.

    Args:
        user_code: The Python code submitted by the user.
        data_file: Path to a parquet file to load as 'df' (optional).

    Returns:
        The full Python script to execute.
    """

    setup_code = """
import sys
import json
import os
import io
import base64
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

# Initialize visualizations list
visualizations = []

# Mock plt.show to capture figures
_original_plt_show = plt.show
def _capture_plt_show(*args, **kwargs):
    if plt.get_fignums():
        for i in plt.get_fignums():
            fig = plt.figure(i)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            visualizations.append({
                "type": "image",
                "format": "png",
                "content": img_base64
            })
            plt.close(fig)
    # Call original (though likely no-op in Agg)
    # _original_plt_show(*args, **kwargs)

plt.show = _capture_plt_show

# Mock plotly show to capture figures
# (This is tricky because plotly figures are objects, usually returned or .show() called)
# We can try to monkeypatch figure.show, but it's an instance method.
# Instead, we'll scan for plotly Figure objects at the end.

# Load data
df = None
"""

    if data_file:
        setup_code += f"""
try:
    # Check if file exists relative to current dir
    data_path = 'data.parquet'
    if os.path.exists(data_path):
        df = pd.read_parquet(data_path)
    else:
        # Fallback to absolute path if provided
        df = pd.read_parquet(r'{data_file}')
except Exception as e:
    print(f"Error loading data: {{e}}", file=sys.stderr)
"""
    else:
        # No data file provided
        setup_code += "\n# No data file loaded\n"

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

# Capture any remaining matplotlib figures not shown
if plt.get_fignums():
    _capture_plt_show()

# Collect variables
variables = {}
import types
for name, val in list(locals().items()):
    if name.startswith('_') or name in ['sys', 'json', 'os', 'io', 'base64', 'pd', 'np', 'scipy', 'sklearn', 'sm', 'plt', 'sns', 'px', 'go', 'pio', 'safe_serialize', 'variables', 'visualizations', '_capture_plt_show', '_original_plt_show']:
        continue
    if isinstance(val, types.ModuleType):
        continue

    # Check for Plotly figures
    if hasattr(val, 'to_json') and (isinstance(val, go.Figure) or 'plotly.graph_objs' in str(type(val))):
        try:
            visualizations.append({
                "type": "plotly",
                "content": json.loads(val.to_json())
            })
            continue # Don't serialize figure as variable
        except:
            pass

    variables[name] = safe_serialize(val)

output = {
    "variables": variables,
    "visualizations": visualizations
}

with open("result.json", "w") as f:
    json.dump(output, f, default=str)
"""

    return setup_code + "\n" + user_code + "\n" + teardown_code
