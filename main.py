import sys
import os
from pathlib import Path

# Add backend directory to sys.path so that 'app' can be imported as a package
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.main import app

# This allows Vercel to find the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
