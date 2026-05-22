"""巡检报告生成器 — 结合设备状态、配置备份、合规检查和性能指标生成 HTML 报告。"""

from datetime import datetime

from ..database import SessionLocal
from ..models.config_archive import ConfigArchive
from ..models.device import Device, DeviceStatus
from ..models.metric import Metric
from ..models.task_record import TaskRecord, TaskStatus


def _query_stats(db) -> dict:
    """Collect all data needed for a report."""
    total = db.query(Device).count()
    online = db.query(Device).filter(Device.status == DeviceStatus.ONLINE).count()
    offline = db.query(Device).filter(Device.status == DeviceStatus.OFFLINE).count()

    today_tasks = db.query(TaskRecord).count()
    failed_tasks = db.query(TaskRecord).filter(TaskRecord.status == TaskStatus.FAILED).count()
    success_tasks = db.query(TaskRecord).filter(TaskRecord.status == TaskStatus.SUCCESS).count()

    # SLA: task success rate
    sla_rate = round(success_tasks / today_tasks * 100, 1) if today_tasks else 100.0

    # Latest metrics per device (CPU example)
    devices = db.query(Device).all()
    device_metrics = []
    for dev in devices:
        metric = db.query(Metric).filter(
            Metric.device_id == dev.id,
            Metric.metric_type == "cpu",
        ).order_by(Metric.collected_at.desc()).first()
        device_metrics.append({
            "name": dev.name,
            "ip": dev.ip_address,
            "status": dev.status.value if dev.status else "unknown",
            "cpu": metric.value if metric else None,
        })

    config_count = db.query(ConfigArchive).count()
    return {
        "total_devices": total,
        "online_devices": online,
        "offline_devices": offline,
        "online_rate": round(online / total * 100, 1) if total else 0,
        "today_tasks": today_tasks,
        "failed_tasks": failed_tasks,
        "success_tasks": success_tasks,
        "sla_rate": sla_rate,
        "device_metrics": device_metrics,
        "config_archives": config_count,
    }


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>NetOps 巡检报告</title>
<style>
body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; max-width: 1000px; margin: 20px auto; padding: 20px; color: #333; }}
h1 {{ color: #1890ff; border-bottom: 2px solid #1890ff; padding-bottom: 8px; }}
h2 {{ color: #001529; margin-top: 24px; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
th, td {{ border: 1px solid #e8e8e8; padding: 8px 12px; text-align: left; font-size: 13px; }}
th {{ background: #fafafa; font-weight: 600; }}
.summary {{ display: flex; gap: 16px; flex-wrap: wrap; }}
.card {{ background: #f6f8fa; border-radius: 8px; padding: 16px; min-width: 120px; text-align: center; }}
.card .num {{ font-size: 28px; font-weight: 700; color: #1890ff; }}
.card .label {{ font-size: 12px; color: #666; }}
.status-online {{ color: #52c41a; font-weight: 600; }}
.status-offline {{ color: #ff4d4f; font-weight: 600; }}
.footer {{ margin-top: 32px; font-size: 11px; color: #999; text-align: center; }}
</style></head>
<body>
<h1>NetOps CMNET 巡检报告</h1>
<p>生成时间: {generated_at}</p>

<h2>设备总览</h2>
<div class="summary">
  <div class="card"><div class="num">{total_devices}</div><div class="label">设备总数</div></div>
  <div class="card"><div class="num" style="color:#52c41a">{online_devices}</div><div class="label">在线</div></div>
  <div class="card"><div class="num" style="color:#ff4d4f">{offline_devices}</div><div class="label">离线</div></div>
  <div class="card"><div class="num">{online_rate}%</div><div class="label">在线率</div></div>
  <div class="card"><div class="num">{today_tasks}</div><div class="label">累计任务</div></div>
  <div class="card"><div class="num" style="color:#52c41a">{success_tasks}</div><div class="label">成功</div></div>
  <div class="card"><div class="num" style="color:#ff4d4f">{failed_tasks}</div><div class="label">失败</div></div>
  <div class="card"><div class="num">{sla_rate}%</div><div class="label">SLA 成功率</div></div>
  <div class="card"><div class="num">{config_archives}</div><div class="label">配置存档</div></div>
</div>

<h2>设备状态详情</h2>
<table>
<tr><th>设备名</th><th>IP</th><th>状态</th><th>CPU 使用率</th></tr>
{device_rows}
</table>

<div class="footer">
  NetOps CMNET - 自动生成 | {generated_at}
</div>
</body></html>"""


def generate_html_report() -> str:
    """Generate a full HTML inspection report."""
    db = SessionLocal()
    try:
        stats = _query_stats(db)
        device_rows = ""
        for d in stats["device_metrics"]:
            cls = "status-online" if d["status"] == "online" else "status-offline"
            cpu = f"{d['cpu']}%" if d["cpu"] is not None else "-"
            device_rows += (
                f"<tr><td>{d['name']}</td><td>{d['ip']}</td>"
                f"<td class='{cls}'>{d['status']}</td><td>{cpu}</td></tr>"
            )
        stats["device_rows"] = device_rows
        stats["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return _HTML_TEMPLATE.format(**stats)
    finally:
        db.close()
