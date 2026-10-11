from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Mission Control")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def main() -> None:
    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
