from __future__ import annotations

import hashlib
import os
import pickle
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import boto3
from fastapi import FastAPI, Request
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = ROOT / "models" / "model.pkl"

model_lock = threading.Lock()


# ---------------------------
# File metadata helpers
# ---------------------------
def file_size_bytes(path: Path) -> Optional[int]:
    try:
        return path.stat().st_size
    except Exception:
        return None


def file_mtime_utc_iso(path: Path) -> Optional[str]:
    try:
        st = path.stat()
        return datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
    except Exception:
        return None


def file_sha256(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):  # 1MB chunks
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def build_model_meta(model: Dict[str, Any], model_path: Path, loaded_ms: int) -> Dict[str, Any]:
    """
    Compute metadata ONCE at load time (or reload time), not per-request.
    """
    sha = file_sha256(model_p
