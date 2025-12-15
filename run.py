"""
Application Entry Point
Run the FastAPI server
"""
import uvicorn
from src.core.config import get_settings


def main():
    """Run the application"""
    settings = get_settings()
    
    print(f"Starting {settings.app_name} v{settings.version}...")
    print(f"Docs: http://{settings.host}:{settings.port}/docs")
    print(f"ReDoc: http://{settings.host}:{settings.port}/redoc")
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
