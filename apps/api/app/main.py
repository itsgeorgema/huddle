from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, demo, graph, groups, sessions
from app.config import get_settings
from app.db.base import init_db
from app.services.observability import metrics_response

settings = get_settings()
app = FastAPI(title="Huddle", description="Conflict-aware deliberation load balancer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(demo.router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "huddle-api"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(metrics_response(), media_type="text/plain; version=0.0.4")
