import os
import shutil
from typing import Callable
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
)(lambda config: ClaudeProvider(config.get("claude", {})))


from providers.opencode import OpenCodeProvider


register(
    pid="opencode_go",
    name="OpenCode Go",
    probe=lambda: (
        os.environ.get("OPENCODE_GO_WORKSPACE_ID", "") != ""
        and os.environ.get("OPENCODE_GO_AUTH_COOKIE", "") != ""
    ),
    requires_auth=True,
)(lambda config: OpenCodeProvider(
    config.get("opencode_go", {}).get("workspace_id") or os.environ.get("OPENCODE_GO_WORKSPACE_ID", ""),
    config.get("opencode_go", {}).get("auth_cookie") or os.environ.get("OPENCODE_GO_AUTH_COOKIE", ""),
))
