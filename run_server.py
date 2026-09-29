import os
import sys
import uvicorn

if __name__ == "__main__":
    # Ensure current directory is in pythonpath
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_dir)
    port = int(os.environ.get("PORT", 8005))
    print(f"Starting 3D ULPIN server on port {port} (0.0.0.0)...")
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
