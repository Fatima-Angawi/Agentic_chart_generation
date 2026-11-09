import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL", "gpt-4o-mini")
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_RETRIES = 2
EXECUTION_TIMEOUT = 30
OUT_PATH_V1 = "chart_v1.png"
OUT_PATH_V2 = "chart_v2.png"