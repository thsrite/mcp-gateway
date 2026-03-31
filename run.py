import uvicorn

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=9000,
        reload=False,
        log_level="info",
    )
