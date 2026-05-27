import shutil
import os
from pathlib import Path


def probe_which(binary: str) -> bool:
    return shutil.which(binary) is not None


def probe_env(var: str) -> bool:
    return os.environ.get(var, "").strip() != ""


def probe_path(path: str) -> bool:
    return Path(path).expanduser().exists()


def scan() -> list:
    from registry import REGISTRY
    return [p for p in REGISTRY if p.probe()]
