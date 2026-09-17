import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_SITE_PACKAGES = os.path.join(BASE_DIR, ".venv", "Lib", "site-packages")

if os.path.exists(VENV_SITE_PACKAGES) and VENV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, VENV_SITE_PACKAGES)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import uvicorn

if __name__ == "__main__":
    print("[INFO] Starting AI Question Bank Backend on http://localhost:8000")
    print("[INFO] Swagger Documentation: http://localhost:8000/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
