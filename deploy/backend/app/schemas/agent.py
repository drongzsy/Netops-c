from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AgentResponse(BaseModel):
    """Unified response envelope for agent-facing APIs."""

    success: bool
    data: Any = None
    error: str | None = None
    meta: dict | None = None


class DiagnoseResult(BaseModel):
    device_id: int
    name: str
    ip_address: str
    device_type: str
    role: str
    status: str
    city: str | None = None
    latest_metrics: list[dict] = []
    config_versions: int = 0
    recent_tasks: list[dict] = []


class NetworkStatus(BaseModel):
    total_devices: int
    online_devices: int
    offline_devices: int
    online_rate: float
    today_tasks: int
    failed_tasks: int
    device_type_distribution: list[dict] = []
    recent_events: list[dict] = []
