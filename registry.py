import os
import shutil
import json
from pathlib import Path
from typing import Callable
from discovery import probe_path
from providers.base import BaseProvider
from providers.claude import ClaudeProvider


class ProviderDef:
    def __init__(self, pid: str, name: str, probe: Callable[[], bool], factory: Callable[[dict], BaseProvider], requires_auth: bool = False):
        self.id = pid
        self.name = name
        self.probe = probe
        self.factory = factory
        self.requires_auth = requires_auth


REGISTRY: list[ProviderDef] = []


def register(pid: str, name: str, probe: Callable[[], bool], requires_auth: bool = False):
    def wrapper(factory: Callable[[dict], BaseProvider]):
        REGISTRY.append(ProviderDef(pid, name, probe, factory, requires_auth))
        return factory
    return wrapper


register(
    pid="claude",
    name="Claude Code",
    probe=lambda: shutil.which("claude") is not None,
)(lambda config: ClaudeProvider(config))

register(
    pid="opencode_go",
    name="OpenCode Go",
    probe=lambda: (
        shutil.which("opencode") is not None
        or os.environ.get("OPENCODE_GO_WORKSPACE_ID", "") != ""
    ),
    requires_auth=True,
)(lambda config: __import__("providers.opencode", fromlist=["OpenCodeProvider"]).OpenCodeProvider(
    workspace_id=config.get("workspace_id") or os.environ.get("OPENCODE_GO_WORKSPACE_ID", ""),
    auth_cookie=config.get("auth_cookie") or os.environ.get("OPENCODE_GO_AUTH_COOKIE", ""),
    api_key=config.get("api_key") or "",
))

register(
    pid="copilot",
    name="GitHub Copilot",
    probe=lambda: probe_path("~/.config/opencode/auth.json"),
    requires_auth=True,
)(lambda config: __import__("providers.copilot", fromlist=["CopilotProvider"]).CopilotProvider(config))

register(
    pid="cursor",
    name="Cursor",
    probe=lambda: probe_path("~/.config/cursor"),
    requires_auth=True,
)(lambda config: __import__("providers.cursor", fromlist=["CursorProvider"]).CursorProvider(config))

register(
    pid="openai",
    name="OpenAI",
    probe=lambda: probe_path("~/.config/opencode/auth.json"),
    requires_auth=True,
)(lambda config: __import__("providers.openai", fromlist=["OpenAIProvider"]).OpenAIProvider(config))

register(
    pid="ollama",
    name="Ollama Cloud Pro",
    probe=lambda: False,
    requires_auth=True,
)(lambda config: __import__("providers.ollama", fromlist=["OllamaProvider"]).OllamaProvider(config.get("cookie", "")))

register(
    pid="zai",
    name="Zai GLM",
    probe=lambda: False,
    requires_auth=True,
)(lambda config: __import__("providers.zai", fromlist=["ZaiProvider"]).ZaiProvider(config.get("api_key", "")))
