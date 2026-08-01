from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .policies import load_policy
import os

from .service import RiskGatewayService

app = FastAPI(title="Content Risk Control Gateway", version="0.1.0")
WEB_DIRECTORY = Path(__file__).resolve().parent.parent / "web"
app.mount("/static", StaticFiles(directory=WEB_DIRECTORY), name="static")


class TextScanRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    policy_id: str = Field(default="eu", description="Set by a trusted application service, never a browser client.")


class ImageScanRequest(BaseModel):
    image_base64: str = Field(min_length=1, description="Base64 image bytes; remote URLs are intentionally not fetched.")
    policy_id: str = Field(default="eu", description="Set by a trusted application service, never a browser client.")


class DemoImageScanRequest(BaseModel):
    categories: list[str] = Field(description="Demo labels only; accepted solely when DEMO_MODE=true.")
    policy_id: str = "eu"


def _service() -> RiskGatewayService:
    return RiskGatewayService(demo_mode=os.getenv("DEMO_MODE", "false").lower() == "true")


def _policy(policy_id: str) -> dict:
    try:
        return load_policy(policy_id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def frontend() -> FileResponse:
    return FileResponse(WEB_DIRECTORY / "index.html")


@app.post("/v1/scan/text")
def scan_text(request: TextScanRequest) -> dict:
    try:
        return _service().scan_text(request.text, _policy(request.policy_id), str(uuid4()))
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/v1/scan/image")
def scan_image(request: ImageScanRequest) -> dict:
    try:
        return _service().scan_image_base64(request.image_base64, _policy(request.policy_id), str(uuid4()))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/v1/demo/scan/image")
def scan_demo_image(request: DemoImageScanRequest) -> dict:
    if os.getenv("DEMO_MODE", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Demo endpoint is disabled.")
    return _service().scan_demo_image(request.categories, _policy(request.policy_id), str(uuid4()))
