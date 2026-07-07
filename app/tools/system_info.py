# app/tools/system_info.py
import platform
import psutil
import subprocess
import sys

async def system_info() -> dict:
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": sys.version,
        "cpu_count": psutil.cpu_count(logical=True),
        "ram_total": round(psutil.virtual_memory().total / (1024**3), 2),  # GB
        "ram_available": round(psutil.virtual_memory().available / (1024**3), 2),
    }
    # GPU info via nvidia-smi if available
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if lines:
                gpu_name, gpu_mem = lines[0].split(',')
                info["gpu"] = gpu_name.strip()
                info["gpu_memory_gb"] = float(gpu_mem.strip()) / 1024
    except:
        info["gpu"] = "Not detected"
    return info