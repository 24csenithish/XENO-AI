# scripts/check_gpu.py
import torch
import subprocess

def check_gpu():
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))
        print("VRAM:", torch.cuda.get_device_properties(0).total_memory / 1e9, "GB")
    else:
        print("CUDA not available. Ollama will use CPU if GPU is not configured.")
    # Check nvidia-smi
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode == 0:
            print("nvidia-smi output available.")
        else:
            print("nvidia-smi not found.")
    except:
        print("nvidia-smi not available.")

if __name__ == "__main__":
    check_gpu()