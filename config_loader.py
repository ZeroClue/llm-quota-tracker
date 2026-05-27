from pathlib import Path
import yaml


CONFIG_DIR = Path.home() / ".config" / "llm-tracker"
CONFIG_PATH = CONFIG_DIR / "config.yaml"
LOCAL_CONFIG_PATH = Path("config.yaml")


def load_config() -> dict:
    path = LOCAL_CONFIG_PATH if LOCAL_CONFIG_PATH.exists() else CONFIG_PATH
    if not path.exists():
        print(f"Config not found at {path}")
        print("Run 'llm-tracker setup' to create one.")
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def resolve_providers(config: dict) -> list:
    from registry import REGISTRY

    from discovery import scan
    discovered = {p.id: p for p in scan()}
    configured = set(config.keys())

    active = []
    seen = set()
    for pid, provider_def in discovered.items():
        if pid in seen:
            continue
        seen.add(pid)
        merged_config = config.get(pid, {})
        provider = provider_def.factory(merged_config)
        active.append(provider)

    for pid in configured:
        if pid not in seen:
            for p in REGISTRY:
                if p.id == pid:
                    provider = p.factory(config[pid] if isinstance(config[pid], dict) else {})
                    active.append(provider)
                    break
    return active
