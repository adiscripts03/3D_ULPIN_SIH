import os
import sys
import uvicorn

if __name__ == "__main__":
    # Ensure current directory is in pythonpath
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000)
