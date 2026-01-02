from __future__ import annotations

import hashlib
import os
import pickle
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import boto3
from fastapi import FastAPI, Request
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]  # repo root (my-mlops-demo/)
DEFAULT_MODEL_PATH = ROOT / "models" / "model.pkl"

# A lock to avoid concurrent reload/read issues
model_lock = threading.Lock()


# ---------------------------
# File metadata helpers
# ---------------------------
def file_size_bytes(path: Path) -> Optional[int]:
    try:
        return path.stat().st_size
    except Exception:
        return None


def file_sha256(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


# ---------------------------
# Optional S3 download support
# ---------------------------
def download_from_s3(s3_uri: str, local_path: Path) -> Path:
    """
    Download s3://bucket/key -> local_path
    """
    u = urlparse(s3_uri)
    if u.scheme != "s3" or not u.netloc or not u.path:
        raise ValueError(f"Invalid S3 URI: {s3_uri}")

    bucket = u.netloc
    key = u.path.lstrip("/")

    local_path.parent.mkdir(parents=True, exist_ok=True)

    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
    s3.download_file(bucket, key, str(local_path))
    return local_path


def resolve_model_path() -> Path:
    """
    Single source of truth for where the model should be loaded from.

    Priority:
      1) MODEL_PATH env var (explicit path inside container/host)
      2) default repo path: ./models/model.pkl

    Optional:
      If MODEL_S3_URI is set, we download it to MODEL_PATH (or MODEL_LOCAL_PATH) before loading.
    """
    # Allow container/compose override (e.g., /tmp/model.pkl)
    env_model_path = os.getenv("MODEL_PATH")
    model_path = Path(env_model_path) if env_model_path else DEFAULT_MODEL_PATH

    # Optional S3: download to model_path (or override with MODEL_LOCAL_PATH)
    s3_uri = os.getenv("MODEL_S3_URI")
    if s3_uri:
        local_override = os.getenv("MODEL_LOCAL_PATH")
        download_target = Path(local_override) if local_override else model_path
        download_from_s3(s3_uri, download_target)
        model_path = download_target

    return model_path


def load_model_from_disk(model_path: Path) -> Dict[str, Any]:
    if not model_path.exists() or model_path.stat().st_size == 0:
        raise RuntimeError(f"Missing/empty model file: {model_path}")
    with model_path.open("rb") as f:
        obj = pickle.load(f)

    # Your code assumes dict-like model with keys like "type", "user_top_products", "global_top_products"
    if not isinstance(obj, dict):
        raise RuntimeError(f"Loaded model is not a dict. Got: {type(obj)}")

    return obj


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = resolve_model_path()
    app.state.model_path = model_path
    app.state.model = load_model_from_disk(model_path)
    yield


app = FastAPI(lifespan=lifespan)


class PredictRequest(BaseModel):
    user_id: int


@app.get("/health")
def health(request: Request):
    # Grab model and path safely
    with model_lock:
        m = request.app.state.model
        model_path: Path = request.app.state.model_path

    sha = file_sha256(model_path)
    size = file_size_bytes(model_path)

    return {
        "status": "ok",
        "model_type": m.get("type", "unknown"),
        "model_path": str(model_path),
        "model_size_bytes": size,
        "model_sha256": sha,
        "model_sha256_short": sha[:8] if sha else None,
    }


@app.post("/predict")
def predict(req: PredictRequest, request: Request):
    with model_lock:
        model = request.app.state.model

    user_recs = model.get("user_top_products", {}).get(req.user_id)
    if user_recs:
        return {
            "user_id": req.user_id,
            "recommendations": user_recs[:5],
            "reason": "personalized",
        }

    return {
        "user_id": req.user_id,
        "recommendations": model.get("global_top_products", [])[:5],
        "reason": "popular_fallback",
    }


@app.post("/reload-model")
def reload_model(request: Request):
    # Re-resolve in case S3 points to a new object or MODEL_PATH changed
    model_path = resolve_model_path()
    new_model = load_model_from_disk(model_path)

    with model_lock:
        request.app.state.model = new_model
        request.app.state.model_path = model_path

    sha = file_sha256(model_path)
    size = file_size_bytes(model_path)

    return {
        "status": "reloaded",
        "model_type": new_model.get("type", "unknown"),
        "model_path": str(model_path),
        "model_size_bytes": size,
        "model_sha256": sha,
        "model_sha256_short": sha[:8] if sha else None,
    }
