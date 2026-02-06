"""
Code Executor Service
Secure sandboxed Python code execution
"""

import ast
import sys
import time
import io
import traceback
from typing import Any, Dict, List, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import numpy as np

from app.config import settings


class CodeExecutor:
    """Execute Python code in a sandboxed environment"""
    
    # Allowed imports for safe execution
    ALLOWED_IMPORTS = {
        'pandas', 'pd',
        'numpy', 'np',
        'scipy', 'stats',
        'sklearn', 'scikit-learn',
        'statsmodels',
        'matplotlib', 'plt',
        'seaborn', 'sns',
        'plotly', 'px', 'go',
        'datetime', 'timedelta',
        'math',
        'statistics',
        'collections', 'Counter', 'defaultdict',
        'itertools',
        'functools',
        'json',
        're',
        'typing'
    }
    
    # Dangerous functions/attributes to block
    BLOCKED_PATTERNS = [
        'eval', 'exec', 'compile', '__import__',
        'open', 'file', 'input',
        'os', 'subprocess', 'sys',
        'socket', 'urllib', 'requests', 'http',
        '__builtins__', '__loader__', '__spec__',
        'globals', 'locals', 'vars', 'dir',
        'getattr', 'setattr', 'delattr', 'hasattr',
        'breakpoint', 'exit', 'quit',
        'pickle', 'shelve', 'marshal',
        'ctypes', 'cffi',
    ]
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate code for security issues.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for syntax errors
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        
        # Check for blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in code:
                return False, f"Blocked pattern detected: {pattern}"
        
        # Validate imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    if module not in self.ALLOWED_IMPORTS:
                        return False, f"Import not allowed: {alias.name}"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    if module not in self.ALLOWED_IMPORTS:
                        return False, f"Import not allowed: {node.module}"
            
            # Check for dangerous function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.BLOCKED_PATTERNS:
                        return False, f"Function not allowed: {node.func.id}"
                
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.BLOCKED_PATTERNS:
                        return False, f"Method not allowed: {node.func.attr}"
        
        return True, None
    
    async def execute(
        self,
        code: str,
        dataframe: Optional[pd.DataFrame] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute Python code in a sandboxed environment.
        
        Args:
            code: Python code to execute
            dataframe: Optional dataframe to make available as 'df'
            timeout: Execution timeout in seconds
        
        Returns:
            Dictionary with execution results
        """
        loop = asyncio.get_event_loop()
        
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    self._execute_sync,
                    code,
                    dataframe
                ),
                timeout=timeout
            )
            return result
        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Execution timed out after {timeout} seconds",
                "stdout": None,
                "stderr": None,
                "result": None,
                "execution_time_ms": timeout * 1000
            }
    
    def _execute_sync(
        self,
        code: str,
        dataframe: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """Synchronous code execution (runs in thread pool)"""
        start_time = time.time()
        
        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = captured_stdout = io.StringIO()
        sys.stderr = captured_stderr = io.StringIO()
        
        # Build execution globals
        exec_globals = {
            '__builtins__': self._get_safe_builtins(),
            'pd': pd,
            'np': np,
            'pandas': pd,
            'numpy': np,
        }
        
        # Add dataframe if provided
        if dataframe is not None:
            exec_globals['df'] = dataframe.copy()
        
        exec_locals = {}
        
        try:
            # Execute code
            exec(code, exec_globals, exec_locals)
            
            # Get result (last expression value if any)
            result = {}
            for key, value in exec_locals.items():
                if not key.startswith('_'):
                    if isinstance(value, pd.DataFrame):
                        result[key] = {
                            "type": "dataframe",
                            "shape": list(value.shape),
                            "columns": value.columns.tolist(),
                            "preview": value.head(10).to_dict(orient='records')
                        }
                    elif isinstance(value, pd.Series):
                        result[key] = {
                            "type": "series",
                            "length": len(value),
                            "preview": value.head(10).to_dict()
                        }
                    elif isinstance(value, np.ndarray):
                        result[key] = {
                            "type": "array",
                            "shape": list(value.shape),
                            "preview": value.flatten()[:20].tolist()
                        }
                    elif isinstance(value, (int, float, str, bool, list, dict)):
                        result[key] = value
                    else:
                        result[key] = str(value)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "result": result,
                "stdout": captured_stdout.getvalue(),
                "stderr": captured_stderr.getvalue(),
                "execution_time_ms": execution_time,
                "visualizations": None  # Would extract from matplotlib/plotly figures
            }
        
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            tb = traceback.format_exc()
            
            return {
                "success": False,
                "error": str(e),
                "result": None,
                "stdout": captured_stdout.getvalue(),
                "stderr": tb,
                "execution_time_ms": execution_time,
                "visualizations": None
            }
        
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def _get_safe_builtins(self) -> Dict[str, Any]:
        """Get a restricted set of safe builtins"""
        import builtins
        
        safe_builtins = {
            # Types
            'int': int,
            'float': float,
            'str': str,
            'bool': bool,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'frozenset': frozenset,
            'bytes': bytes,
            'bytearray': bytearray,
            'complex': complex,
            'type': type,
            'object': object,
            # Functions
            'len': len,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sorted': sorted,
            'reversed': reversed,
            'min': min,
            'max': max,
            'sum': sum,
            'abs': abs,
            'round': round,
            'pow': pow,
            'divmod': divmod,
            'all': all,
            'any': any,
            'print': print,
            'repr': repr,
            'format': format,
            'isinstance': isinstance,
            'issubclass': issubclass,
            'callable': callable,
            'iter': iter,
            'next': next,
            'slice': slice,
            'hash': hash,
            'id': id,
            'hex': hex,
            'oct': oct,
            'bin': bin,
            'ord': ord,
            'chr': chr,
            'ascii': ascii,
            # Exceptions
            'Exception': Exception,
            'ValueError': ValueError,
            'TypeError': TypeError,
            'KeyError': KeyError,
            'IndexError': IndexError,
            'AttributeError': AttributeError,
            'ZeroDivisionError': ZeroDivisionError,
            'StopIteration': StopIteration,
            # Constants
            'True': True,
            'False': False,
            'None': None,
        }
        
        return safe_builtins
