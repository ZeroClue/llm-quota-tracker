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
