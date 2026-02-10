"""
Beagle Execution Server
Runs inside the sandbox container to provide stateful code execution
"""

import sys
import io
import os
import json
import traceback
import base64
import contextlib
import types
from typing import Dict, Any, List

from flask import Flask, request, jsonify

# Data Science Libraries (pre-imported for speed)
import pandas as pd
import numpy as np
import scipy.stats
import sklearn
import statsmodels.api as sm
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# Configure Matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

# Global execution context (variables persist here)
EXECUTION_GLOBALS = {}
# Add standard imports to globals
EXECUTION_GLOBALS.update({
    'pd': pd,
    'np': np,
    'scipy': scipy,
    'sklearn': sklearn,
    'sm': sm,
    'plt': plt,
    'sns': sns,
    'px': px,
    'go': go,
    'pio': pio,
    'os': os,
    'sys': sys,
    'json': json
})

# Visualization capture
visualizations = []

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

# Patch plt.show
plt.show = _capture_plt_show

def safe_serialize(obj):
    """Serialize objects for JSON response, handling DataFrames/Arrays specially"""
    if isinstance(obj, (pd.DataFrame, pd.Series)):
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
    elif isinstance(obj, (int, float, str, bool, list, dict, tuple, type(None))):
        try:
            # Ensure JSON serializable
            json.dumps(obj)
            return obj
        except:
            return str(obj)
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    else:
        return str(obj)

@app.route('/execute', methods=['POST'])
def execute_code():
    global visualizations
    visualizations = []  # Reset for this run

    data = request.json
    code = data.get('code', '')
    data_path = data.get('data_path') # Path inside container (e.g., /app/data.parquet)

    # Capture stdout/stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Load data if provided and not already loaded (or reload?)
    # Stateful: If data_path provided, load it as 'df'.
    if data_path:
        try:
            if os.path.exists(data_path):
                # We always reload if path provided, assuming user wants fresh data
                # Or check if 'df' exists? No, explicit reload is safer.
                df = pd.read_parquet(data_path)
                EXECUTION_GLOBALS['df'] = df
            else:
                print(f"Data file not found: {data_path}", file=stderr_capture)
        except Exception as e:
            print(f"Error loading data: {e}", file=stderr_capture)

    success = True
    result_variables = {}

    with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
        try:
            # Execute code in global context
            exec(code, EXECUTION_GLOBALS)
        except Exception:
            success = False
            traceback.print_exc()

    # Capture remaining plots
    if plt.get_fignums():
        _capture_plt_show()

    # Serialize variables (only new or modified ones, technically all locals are in globals)
    # We return everything that isn't a module or hidden
    for name, val in list(EXECUTION_GLOBALS.items()):
        if name.startswith('_') or isinstance(val, types.ModuleType) or isinstance(val, types.FunctionType):
            continue
        if name in ['safe_serialize', 'visualizations', '_capture_plt_show', 'EXECUTION_GLOBALS']:
            continue

        # Check for Plotly figures
        if hasattr(val, 'to_json') and (isinstance(val, go.Figure) or 'plotly.graph_objs' in str(type(val))):
            try:
                visualizations.append({
                    "type": "plotly",
                    "content": json.loads(val.to_json())
                })
                continue
            except:
                pass

        # Limit what we send back to avoid huge payloads
        # Only send small objects or metadata
        try:
            result_variables[name] = safe_serialize(val)
        except:
            result_variables[name] = str(val)

    return jsonify({
        "success": success,
        "stdout": stdout_capture.getvalue(),
        "stderr": stderr_capture.getvalue(),
        "variables": result_variables,
        "visualizations": visualizations
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
