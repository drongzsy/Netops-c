"""Async Syslog 接收服务器 — 监听 UDP 端口接收设备日志并入库。

支持标准 RFC 3164/5424 syslog 格式，从 eNSP 设备接收日志消息后
解析并持久化到数据库，供 Web UI 查询和分析。
"""

import asyncio
import logging
import re
import os
from datetime import datetime

from ..database import SessionLocal
from ..models.syslog import SyslogEntry

_logger = logging.getLogger(__name__)

# RFC 3164 syslog parser: <PRI>TIMESTAMP HOSTNAME MSG
_SYSLOG_RE = re.compile(
    r"<(\d{1,3})>"                          # PRI
    r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"  # TIMESTAMP (e.g. "May 22 14:30:00")
    r"\s+(\S+)"                              # HOSTNAME
    r"\s+(.*)"                               # MSG
)

# Severity levels (RFC 5424)
SEVERITY_MAP = [
    "emergency", "alert", "critical", "error",
    "warning", "notice", "info", "debug",
]

# Facility names (RFC 5424)
FACILITY_MAP = {
    0: "kern", 1: "user", 2: "mail", 3: "daemon",
    4: "auth", 5: "syslog", 6: "lpr", 7: "news",
    8: "uucp", 9: "cron", 10: "authpriv", 11: "ftp",
    16: "local0", 17: "local1", 18: "local2", 19: "local3",
    20: "local4", 21: "local5", 22: "local6", 23: "local7",
}


def _parse_priority(pri: int) -> tuple[str, str]:
    """Extract facility and severity from syslog priority value."""
    facility_code = pri // 8
    severity_code = pri % 8
    facility = FACILITY_MAP.get(facility_code, str(facility_code))
    severity = SEVERITY_MAP[severity_code] if severity_code < len(SEVERITY_MAP) else str(severity_code)
    return facility, severity


def _parse_timestamp(ts_str: str) -> datetime | None:
    """Parse syslog timestamp (e.g. 'May 22 14:30:00') to datetime."""
    try:
        now = datetime.utcnow()
        parsed = datetime.strptime(ts_str, "%b %d %H:%M:%S")
        return parsed.replace(year=now.year)
    except ValueError:
        return None


def _parse_syslog(raw: str) -> dict:
    """Parse a raw syslog message into structured fields."""
    m = _SYSLOG_RE.match(raw.strip())
    if not m:
        return {"raw": raw}

    pri = int(m.group(1))
    ts_str = m.group(2)
    hostname = m.group(3)
    msg = m.group(4)

    facility, severity = _parse_priority(pri)
    app_name = msg.split(":")[0] if ":" in msg[:40] else None

    return {
        "facility": facility,
        "severity": severity,
        "timestamp": _parse_timestamp(ts_str),
        "hostname": hostname,
        "app_name": app_name,
        "message": msg,
        "raw": raw.strip(),
    }


class SyslogServer:
    """Async UDP syslog receiver.

    Usage:
        server = SyslogServer(port=514)
        await server.start()  # runs in background
        # ...
        await server.stop()
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 514):
        self.host = os.getenv("SYSLOG_HOST", host)
        self.port = int(os.getenv("SYSLOG_PORT", str(port)))
        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: asyncio.DatagramProtocol | None = None

    async def _on_message(self, data: bytes, addr: tuple) -> None:
        """Process a received syslog message."""
        raw = data.decode("utf-8", errors="replace")
        parsed = _parse_syslog(raw)
        if not parsed.get("hostname"):
            return

        db = SessionLocal()
        try:
            entry = SyslogEntry(
                facility=parsed.get("facility"),
                severity=parsed.get("severity"),
                timestamp=parsed.get("timestamp"),
                hostname=parsed.get("hostname"),
                app_name=parsed.get("app_name"),
                message=parsed.get("message", raw),
                raw=raw,
            )
            db.add(entry)
            db.commit()
        except Exception:
            pass
        finally:
            db.close()

    async def start(self) -> None:
        """Start the UDP syslog receiver."""
        try:
            loop = asyncio.get_event_loop()
            self._transport, self._protocol = await loop.create_datagram_endpoint(
                lambda: _SyslogProtocol(self._on_message),
                local_addr=(self.host, self.port),
            )
            _logger.info(f"Syslog server listening on udp://{self.host}:{self.port}")
        except PermissionError:
            _logger.warning(
                f"Cannot bind to port {self.port} (privileged). "
                "Try SYSLOG_PORT=5140 or run with elevated privileges."
            )
        except Exception as e:
            _logger.warning(f"Syslog server failed to start: {e}")

    async def stop(self) -> None:
        """Stop the syslog receiver."""
        if self._transport:
            self._transport.close()
            _logger.info("Syslog server stopped")


class _SyslogProtocol(asyncio.DatagramProtocol):
    """Internal UDP protocol handler for syslog messages."""

    def __init__(self, callback):
        self._callback = callback

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        asyncio.ensure_future(self._callback(data, addr))

    def error_received(self, exc: Exception) -> None:
        _logger.error(f"Syslog UDP error: {exc}")


# Singleton instance
syslog_server = SyslogServer()
