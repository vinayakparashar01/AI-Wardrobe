import os
import uvicorn

from app.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    is_dev = os.environ.get("ENVIRONMENT", "development").lower() in ("development", "dev", "local")
    uvicorn.run("app.app:app", host=host, port=port, reload=is_dev)
