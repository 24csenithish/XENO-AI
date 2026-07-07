# app/tools/python_tool.py
import subprocess
import tempfile
import os
from app.config import settings

async def execute_python(code: str) -> dict:
    if not settings.ENABLE_PYTHON_TOOL:
        return {"error": "Python tool is disabled by configuration."}
    # Write code to temporary file and run with timeout
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        f.flush()
        try:
            result = subprocess.run(
                ["python", f.name],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=tempfile.gettempdir()
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out"}
        finally:
            os.unlink(f.name)