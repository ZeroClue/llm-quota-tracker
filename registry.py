from typing import Callable
from providers.base import BaseProvider


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
