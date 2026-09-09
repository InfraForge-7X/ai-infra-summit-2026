from fastapi import FastAPI

from src.api.routes.routing import router as routing_router

app = FastAPI(title="AFRI-EDGE", version="0.1.0")
app.include_router(routing_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "afri-edge"}
