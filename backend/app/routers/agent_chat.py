"""Agent Chat — natural language and tool-calling endpoints for AI agents."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..database import get_db
from ..schemas.agent import AgentResponse
from ..services.agent_tools import TOOL_DEFINITIONS, execute_tool
from .agent import agent_auth

router = APIRouter(prefix="/api/agent", tags=["agent"], dependencies=[Depends(agent_auth)])


class ToolCallRequest(BaseModel):
    """A single tool execution request from an LLM."""
    tool: str
    arguments: dict = {}


class ChatRequest(BaseModel):
    """Natural language chat request."""
    message: str
    history: list[dict] = []


# ── Tool discovery ──────────────────────────────────────────────────────


@router.get("/tools/definitions")
def get_tool_definitions():
    """Return all tool definitions in OpenAI Function Calling format.

    AI agents should call this first to discover available operations.
    Compatible with Claude Tool Use, OpenAI Function Calling, and similar.
    """
    return AgentResponse(
        success=True,
        data={
            "tools": TOOL_DEFINITIONS,
            "instructions": (
                "You are a network operations AI assistant for CMNET carrier-grade network. "
                "You can manage Huawei CE CloudEngine devices via Ansible automation. "
                "Available operations include: device query, config backup/restore/diff, "
                "compliance checking, metrics monitoring, and CLI command execution. "
                "For destructive operations (push config, reboot), always ask for user confirmation first."
            ),
        },
    )


# ── Tool execution ──────────────────────────────────────────────────────


@router.post("/tools/execute")
async def execute_tool_call(data: ToolCallRequest):
    """Execute a tool call from an LLM.

    Accepts a tool name and arguments matching one of the tool definitions
    from ``/api/agent/tools/definitions``. Routes the call to the appropriate
    Agent API endpoint and returns structured results.
    """
    result = await execute_tool(data.tool, data.arguments)
    return AgentResponse(success=result.get("success", False), data=result)


@router.post("/chat")
async def agent_chat(data: ChatRequest):
    """Natural language entry point for AI agent operations.

    Accepts plain text instructions like:
    - "检查全网设备状态"
    - "备份 PB-1 的配置"
    - "看看有没有异常"

    The agent should parse the intent, map to the appropriate tool(s),
    execute them, and return a human-readable response.
    """
    return AgentResponse(
        success=True,
        data={
            "message": (
                f"Received: '{data.message}'. "
                "Use /api/agent/tools/definitions to discover available tools, "
                "then call /api/agent/tools/execute to perform operations."
            ),
            "available_tools": len(TOOL_DEFINITIONS),
        },
    )
