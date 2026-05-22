"""Phase 5 路由 — 智能巡检 + 故障分析 API。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.agent import AgentResponse
from .agent import agent_auth

router = APIRouter(prefix="/api/inspection", tags=["inspection"], dependencies=[Depends(agent_auth)])


@router.post("/run")
def trigger_inspection():
    """触发全量巡检：备份 + 性能采集 + 合规检查一次性执行。"""
    from ..services.ai_inspection import run_full_inspection
    result = run_full_inspection()
    return AgentResponse(success=True, data=result)


@router.get("/report")
def get_analysis_report():
    """获取智能分析报告（基于已有数据，不触发新任务）。"""
    from ..services.ai_inspection import generate_analysis_report
    report = generate_analysis_report()
    return AgentResponse(success=True, data=report)


@router.get("/fault/{device_id}")
def fault_analysis(device_id: int, hours: int = 24):
    """对指定设备进行多维度故障关联分析。"""
    from ..services.fault_analysis import analyze_device
    result = analyze_device(device_id, hours=hours)
    return AgentResponse(success=True, data=result)
