import os
import subprocess
import sys
from app import config

WORKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worker.py")


def run_code(code, data_path, job_dir, out_path):
    code_path = os.path.join(job_dir, "generated_code.py")
    with open(code_path, "w", encoding="utf-8") as f:
        f.write(code)

    env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
    env.update({"MPLBACKEND": "Agg", "MPLCONFIGDIR": job_dir, "PYTHONIOENCODING": "utf-8"})

    try:
        result = subprocess.run(
            [sys.executable, WORKER_PATH, code_path, data_path],
            cwd=job_dir,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=config.EXECUTION_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Execution timed out"}

    if result.returncode == 0 and os.path.exists(os.path.join(job_dir, out_path)):
        return {"success": True, "error": None}
    return {"success": False, "error": (result.stdout + result.stderr).strip()}