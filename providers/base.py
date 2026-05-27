from dataclasses import dataclass, field
from typing import Optional
from abc import ABC, abstractmethod


@dataclass
class QuotaWindow:
    label: str
    pct_used: Optional[float] = None
    resets_in: Optional[str] = None


@dataclass
class ProviderState:
    name: str
    provider_type: str  # "budget" or "burst"

    # Budget fields
    remaining_quota: Optional[float] = None
    total_quota: Optional[float] = None
    days_until_reset: Optional[int] = None
    unit: str = "$"

    # Burst fields
    window_pct_used: Optional[float] = None
    window_resets_in: Optional[str] = None

    # Additional windows (multi-window display)
    windows: list[QuotaWindow] = field(default_factory=list)

    # Calculated fields
    daily_allowance: Optional[float] = None
    current_pace: Optional[float] = None
    status: str = "ok"  # ok, warning, critical, needs-auth


class BaseProvider(ABC):
    @abstractmethod
    def fetch(self) -> ProviderState:
        ...
