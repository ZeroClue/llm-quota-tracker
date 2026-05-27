import shutil
import os
from pathlib import Path
from registry import REGISTRY, ProviderDef


def probe_which(binary: str) -> bool:
    return shutil.which(binary) is not None


def probe_env(var: str) -> bool:
    return os.environ.get(var, "").strip() != ""


def probe_path(path: str) -> bool:
    return Path(path).expanduser().exists()


def scan() -> list[ProviderDef]:
    return [p for p in REGISTRY if p.probe()]
