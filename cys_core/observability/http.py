from __future__ import annotations

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


def render_metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def mount_metrics(app: FastAPI) -> None:
    @app.get("/metrics")
    async def get_metrics() -> Response:
        return render_metrics()
