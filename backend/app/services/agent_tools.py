"""AI Agent tool definitions — wraps Agent API as LLM-callable tools.

Each tool follows OpenAI Function Calling format so any LLM (Claude, GPT, etc.)
can discover and call network operations functions through a unified interface.
"""

import httpx

from ..config import AGENT_API_KEY

AGENT_BASE = "http://localhost:8000/api/agent"

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "network_status",
            "description": "获取全网设备健康状态总览（设备总数、在线率、今日任务、异常数、设备类型分布）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_devices",
            "description": "查询设备列表，可按类型、城市、状态过滤",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_type": {
                        "type": "string",
                        "enum": ["BB", "PB", "MB", "BRAS", "RR", "PE", "PC", "SW", "SR", "FW"],
                        "description": "设备类型：BB-集团骨干 PB-省网核心 MB-城域核心 BRAS-业务接入 RR-路由反射 PE-客户边缘 PC-自有业务 SW-管理交换机",
                    },
                    "city": {"type": "string", "description": "所在地市，如 武汉/襄阳"},
                    "status": {"type": "string", "enum": ["online", "offline", "unknown"], "description": "设备状态"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "diagnose_device",
            "description": "一键诊断指定设备：返回设备详情、最新性能指标、配置版本数、近期任务历史",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "integer", "description": "设备ID"},
                },
                "required": ["device_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "backup_device",
            "description": "对指定设备执行配置备份",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "设备ID列表，如 [1, 2, 3]",
                    },
                },
                "required": ["device_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "backup_all_devices",
            "description": "一键备份所有在线设备的 running-config",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compliance_check",
            "description": "对指定设备执行合规检查（BGP 邻居状态、SNMP Community 安全、ACL 规则、NTP 配置）",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "设备ID列表",
                    },
                },
                "required": ["device_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compliance_all_devices",
            "description": "一键检查所有在线设备的配置合规性",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_task_result",
            "description": "查询异步任务的执行结果和详细输出",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "任务ID"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_commands",
            "description": "在指定设备上执行一条或多条 CLI 命令，用于批量配置和故障排查",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "目标设备ID列表",
                    },
                    "commands": {
                        "type": "string",
                        "description": "要执行的命令，多条命令用换行分隔",
                    },
                },
                "required": ["device_ids", "commands"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_device_config",
            "description": "查看设备指定历史版本的配置内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "integer", "description": "设备ID"},
                    "version": {"type": "string", "description": "配置版本号，如 20260522_142530"},
                },
                "required": ["device_id", "version"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_config",
            "description": "对比设备两个配置版本的差异，返回增删改的详细内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "integer", "description": "设备ID"},
                    "from_version": {"type": "string", "description": "旧版本号"},
                    "to_version": {"type": "string", "description": "新版本号"},
                },
                "required": ["device_id", "from_version", "to_version"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_metrics",
            "description": "查看设备的 CPU 或内存使用率趋势数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "integer", "description": "设备ID"},
                    "metric_type": {
                        "type": "string",
                        "enum": ["cpu", "memory"],
                        "description": "指标类型",
                    },
                    "hours": {
                        "type": "integer",
                        "description": "查询最近 N 小时的数据",
                    },
                },
                "required": ["device_id", "metric_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "full_inspection",
            "description": "执行全网一键巡检：配置备份 + 性能采集 + 合规检查一次性完成",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

_TOOL_ROUTES: dict[str, tuple[str, str, dict | None]] = {
    "network_status": ("GET", f"{AGENT_BASE}/network/status", None),
    "list_devices": ("GET", f"{AGENT_BASE}/devices", None),
    "diagnose_device": ("GET", f"{AGENT_BASE}/devices/{{device_id}}/diagnose", None),
    "backup_device": ("POST", f"{AGENT_BASE}/tasks", {"task_type": "backup"}),
    "backup_all_devices": ("POST", f"{AGENT_BASE}/tasks/backup-all", None),
    "compliance_check": ("POST", f"{AGENT_BASE}/tasks", {"task_type": "compliance"}),
    "compliance_all_devices": ("POST", f"{AGENT_BASE}/tasks/compliance-all", None),
    "get_task_result": ("GET", f"{AGENT_BASE}/tasks/{{task_id}}", None),
    "run_commands": ("POST", f"{AGENT_BASE}/tasks", {"task_type": "push"}),
    "get_device_config": ("GET", f"{AGENT_BASE}/devices/{{device_id}}/config/{{version}}", None),
    "compare_config": ("GET", f"{AGENT_BASE}/configs/{{device_id}}/diff", None),
    "get_metrics": ("GET", f"{AGENT_BASE}/monitor/{{device_id}}", None),
    "full_inspection": ("POST", f"{AGENT_BASE}/tasks/backup-all", None),
}

_SCRUBBED_PARAMS = {"task_id", "device_id", "device_ids", "version", "from_version", "to_version"}


def _inject_path_params(path: str, args: dict) -> str:
    for key in list(args):
        placeholder = f"{{{{{key}}}}}"
        if placeholder in path:
            path = path.replace(placeholder, str(args.pop(key)))
    return path


async def execute_tool(name: str, arguments: dict) -> dict:
    """Execute a tool call by routing to the corresponding Agent API endpoint."""
    route = _TOOL_ROUTES.get(name)
    if not route:
        return {"success": False, "error": f"Unknown tool: {name}"}

    method, path, body_template = route
    headers = {"X-API-Key": AGENT_API_KEY} if AGENT_API_KEY else {}

    # Clone args; inject path params, keep query params
    args = dict(arguments)
    path = _inject_path_params(path, args)

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                resp = await client.get(path, headers=headers, params=args)
            else:
                body = dict(body_template or {})
                # Merge remaining args into body (skip path-scrubbed params)
                for k, v in args.items():
                    if k not in _SCRUBBED_PARAMS:
                        body[k] = v
                # device_ids always goes in body for POST
                if "device_ids" in arguments:
                    body["device_ids"] = arguments["device_ids"]
                if "commands" in arguments:
                    body["extra_vars"] = {"config_lines": arguments["commands"].split("\n")}
                resp = await client.post(path, headers=headers, json=body)
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
