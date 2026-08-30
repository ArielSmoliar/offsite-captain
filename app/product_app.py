"""Standalone product surface for local review and Cloud Run deployment."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.product_api import router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="Offsite Captain",
    description="Operator-facing offsite coordination and authorization workflow.",
)
app.include_router(router)


@app.get("/healthz", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", include_in_schema=False)
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/", include_in_schema=False)
def product_home() -> RedirectResponse:
    return RedirectResponse(url="/product/")


app.mount(
    "/product", StaticFiles(directory=FRONTEND_DIR, html=True), name="product"
)
