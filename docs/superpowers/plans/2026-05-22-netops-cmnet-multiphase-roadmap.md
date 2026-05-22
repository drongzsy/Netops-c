# NetOps CMNET — 多阶段开发路线图

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**项目目标:** 基于 Ansible + Web UI + AI Agent，实现对 eNSP 华为模拟器内 CMNET 城域网设备的运维管理仿真，最终通过 AI 智能体完成网络设备运维操作。

**架构定位:** Ansible (执行引擎) + 自研层 (业务逻辑/AI接入) + 开源组件 (监控/日志/IPAM)

**参考平台:** 华为 eSight、SolarWinds NPM、Zabbix、锐捷 RIIL

---

## 总体进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| **Phase 1: 基础框架** | Ansible整合 + CRUD + Web UI + Auth | ✅ **已完成** |
| **Phase 2: AI + 运维增强** | AI Agent接入层 + 批量命令 + 定时任务 + 测试 | 🔄 **当前阶段** |
| **Phase 3: 资源与报表** | IPAM + 链路管理 + 巡检报告 + VLAN | 📋 待开始 |
| **Phase 4: 监控与告警** | 告警引擎 + 延迟监控 + SLA + 报表 | 📋 待开始 |
| **Phase 5: 日志与智能** | Syslog接收 + 故障辅助 + 智能巡检 | 📋 远期规划 |

---

## Phase 1: 基础框架 ✅ 已完成

### 交付内容

| 维度 | 功能 | 状态 |
|------|------|------|
| 运维操作 | Ansible 4 个 Playbook (备份/采集/合规/下发) | ✅ |
| 资源管理 | 设备台账 CRUD、凭据管理 | ✅ |
| 资源管理 | 设备拓扑 (SVG 可视化) | ✅ |
| 监控告警 | CPU/内存/接口性能采集 (Ansible) | ✅ |
| 报表分析 | 性能趋势图表 (ECharts) | ✅ |
| 安全 | JWT 认证、bcrypt 密码、Fernet 凭据加密 | ✅ |
| AI 接口 | Agent API (10端点 + 统一响应 + 双模认证) | ✅ |
| 测试 | 单元测试 (34 tests passing) | ✅ |
| 工程 | Git 初始化、MySQL 迁移 | ✅ |

### Codebase

```
Backend:  2,080 lines Python (7 models + 8 routers + 7 services)
Frontend: 1,593 lines Vue/JS (7 views + 3 components)
Ansible:   119 lines YAML (4 playbooks)
Tests:     34 tests, all passing
```

---

## Phase 2: AI 接入层 + 运维增强 🔄 当前阶段

### 目标

打通 AI 智能体到网络设备的完整链路，补全日常运维必备操作。

### Task 2.1: AI 智能体完整接入层 (P0)

**文件:**
- Create: `backend/app/services/agent_tools.py`
- Create: `backend/app/services/nl_parser.py`
- Create: `backend/app/routers/agent_chat.py`
- Create: `backend/app/models/agent_session.py`

- [ ] **Step 1: 创建 Tool Definitions**

LLM 无法直接调用 REST API。需要将 Agent API 的每个端点包装为 OpenAI/Anthropic Function Calling 格式的 Tool Definition。

```python
# app/services/agent_tools.py
"""AI Agent tool definitions — wraps Agent API as LLM-callable tools."""

from typing import Any


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "network_status",
            "description": "获取全网设备健康状态总览（设备总数、在线率、今日任务、异常）",
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
                    "device_type": {"type": "string", "enum": ["BB","PB","MB","BRAS","RR","PE","PC","SW","SR","FW"], "description": "设备类型"},
                    "city": {"type": "string", "description": "所在地市"},
                    "status": {"type": "string", "enum": ["online","offline","unknown"], "description": "设备状态"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "diagnose_device",
            "description": "一键诊断指定设备，返回设备信息、最新性能指标、配置版本数、近期任务",
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
                    "device_ids": {"type": "array", "items": {"type": "integer"}, "description": "设备ID列表"},
                },
                "required": ["device_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "backup_all_devices",
            "description": "一键备份所有在线设备的配置",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compliance_check",
            "description": "对指定设备执行合规检查（BGP/SNMP/ACL/NTP）",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_ids": {"type": "array", "items": {"type": "integer"}, "description": "设备ID列表"},
                },
                "required": ["device_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compliance_all",
            "description": "一键检查所有在线设备的配置合规性",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_task_result",
            "description": "查询任务执行结果",
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
            "name": "execute_command",
            "description": "在设备上执行一条或多条 CLI 命令",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_ids": {"type": "array", "items": {"type": "integer"}, "description": "目标设备ID列表"},
                    "commands": {"type": "string", "description": "要执行的命令，多条用换行分隔"},
                },
                "required": ["device_ids", "commands"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_device_config",
            "description": "查看设备指定版本的配置内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "integer", "description": "设备ID"},
                    "version": {"type": "string", "description": "配置版本号"},
                },
                "required": ["device_id", "version"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_config",
            "description": "对比设备两个版本的配置差异",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "integer", "description": "设备ID"},
                    "from_version": {"type": "string", "description": "旧版本"},
                    "to_version": {"type": "string", "description": "新版本"},
                },
                "required": ["device_id", "from_version", "to_version"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_metrics",
            "description": "查看设备的性能指标趋势（CPU/内存）",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "integer", "description": "设备ID"},
                    "metric_type": {"type": "string", "enum": ["cpu", "memory"], "description": "指标类型"},
                    "hours": {"type": "integer", "description": "查询最近N小时", "default": 24},
                },
                "required": ["device_id", "metric_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_inspection",
            "description": "执行全网巡检：备份 + 采集 + 合规检查一次性完成",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# Tool execution router — maps tool name → Agent API endpoint
import httpx

AGENT_BASE = "http://localhost:8000/api/agent"
AGENT_API_KEY = None  # Set from config

async def execute_tool(name: str, arguments: dict) -> dict:
    """Execute a tool call and return the result."""
    from ..config import AGENT_API_KEY as KEY
    headers = {"X-API-Key": KEY} if KEY else {}
    async with httpx.AsyncClient() as client:
        route_map = {
            "network_status": ("GET", f"{AGENT_BASE}/network/status"),
            "list_devices": ("GET", f"{AGENT_BASE}/devices"),
            "diagnose_device": ("GET", f"{AGENT_BASE}/devices/{arguments['device_id']}/diagnose"),
            "backup_device": ("POST", f"{AGENT_BASE}/tasks", {"task_type": "backup", "device_ids": arguments["device_ids"]}),
            "backup_all_devices": ("POST", f"{AGENT_BASE}/tasks/backup-all"),
            "compliance_check": ("POST", f"{AGENT_BASE}/tasks", {"task_type": "compliance", "device_ids": arguments["device_ids"]}),
            "compliance_all": ("POST", f"{AGENT_BASE}/tasks/compliance-all"),
            "get_task_result": ("GET", f"{AGENT_BASE}/tasks/{arguments['task_id']}"),
            "execute_command": ("POST", f"{AGENT_BASE}/tasks", {"task_type": "push", **arguments}),
            "get_device_config": ("GET", f"{AGENT_BASE}/devices/{arguments['device_id']}/config/{arguments['version']}"),
            "compare_config": ("GET", f"{AGENT_BASE}/configs/{arguments['device_id']}/diff"),
            "get_metrics": ("GET", f"{AGENT_BASE}/monitor/{arguments['device_id']}"),
            "run_inspection": ("POST", f"{AGENT_BASE}/tasks/backup-all"),
        }
        method, path = route_map[name][:2]
        body = route_map[name][2] if len(route_map[name]) > 2 else None
        if method == "GET":
            resp = await client.get(path, headers=headers, params={k: v for k, v in arguments.items() if k not in ("device_id", "task_id")})
        else:
            resp = await client.post(path, headers=headers, json=body or arguments)
        return resp.json()
```

- [ ] **Step 2: 创建自然语言指令入口**

```python
# app/routers/agent_chat.py
"""Chat-style endpoint — AI agent sends natural language, system responds with action results."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..schemas.agent import AgentResponse
from ..services.agent_tools import TOOL_DEFINITIONS, execute_tool

router = APIRouter(prefix="/api/agent", tags=["agent"])

class ChatRequest(BaseModel):
    message: str
    history: list = []

class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict = {}

@router.post("/tools/definitions")
def get_tool_definitions():
    """Return tool definitions in OpenAI/Anthropic format for LLM consumption."""
    return AgentResponse(success=True, data={"tools": TOOL_DEFINITIONS})

@router.post("/tools/execute")
async def execute_tool_call(data: ToolCallRequest):
    """Execute a tool call from an LLM and return the result."""
    try:
        result = await execute_tool(data.tool, data.arguments)
        return AgentResponse(success=True, data=result)
    except Exception as e:
        return AgentResponse(success=False, error=str(e))
```

- [ ] **Step 3: 创建操作确认工作流**

```python
# app/models/agent_session.py
from sqlalchemy import Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func
from ..database import Base

class AgentSession(Base):
    __tablename__ = "agent_sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    tool_name = Column(String(64), nullable=False)
    input_params = Column(JSON, nullable=True)
    output_result = Column(JSON, nullable=True)
    status = Column(String(16), default="pending")  # pending/approved/rejected/completed/error
    approved_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
```

- [ ] **Step 4: 测试 AI Agent 工具调用链路**

启动后端并用 Python 测试工具执行：

```python
import httpx, json
resp = httpx.get("http://localhost:8000/api/agent/tools/definitions",
                 headers={"X-API-Key": "cmnet-agent-key-2026"})
tools = resp.json()["data"]["tools"]
print(f"Tool definitions: {len(tools)} tools loaded")

resp = httpx.get("http://localhost:8000/api/agent/tools/execute",
                 headers={"X-API-Key": "cmnet-agent-key-2026"},
                 json={"tool": "network_status", "arguments": {}})
print(f"Network status: {resp.json()}")
```

Expected: 13 tools loaded, network status returns device data

- [ ] **Step 5: 运行测试确认**

Run: `cd backend && pytest tests/ -v`

Expected: ALL tests pass (35+ tests)

- [ ] **Step 6: 提交**

Run: `git add backend/app/services/agent_tools.py backend/app/routers/agent_chat.py backend/app/models/agent_session.py backend/app/models/__init__.py && git commit -m "feat: add AI Agent tool layer with NL entry and confirmation workflow"`

---

### Task 2.2: 批量命令执行 (P0)

**文件:**
- Modify: `ansible/playbooks/push_config.yml`
- Create: `backend/app/routers/commands.py`

- [ ] **Step 1: 新增批量命令 Playbook**

```yaml
# ansible/playbooks/run_commands.yml
- name: Run arbitrary commands on devices
  hosts: all
  gather_facts: no
  tasks:
    - name: Execute CLI commands
      ansible.netcommon.cli_command:
        command: "{{ item }}"
      register: cmd_results
      loop: "{{ commands | default([]) }}"

    - name: Aggregate results
      set_fact:
        all_outputs: "{{ cmd_results.results | map(attribute='stdout') | list }}"
```

- [ ] **Step 2: 添加到 TaskType 枚举**

In `models/task_record.py`:
```python
class TaskType(str, enum.Enum):
    BACKUP = "backup"
    PUSH = "push"
    COLLECT = "collect"
    COMPLIANCE = "compliance"
    COMMAND = "command"  # ADDED
```

In `services/task_manager.py`:
```python
_PLAYBOOK_MAP = {
    TaskType.BACKUP: "backup.yml",
    TaskType.COLLECT: "collect_metrics.yml",
    TaskType.COMPLIANCE: "compliance_check.yml",
    TaskType.PUSH: "push_config.yml",
    TaskType.COMMAND: "run_commands.yml",  # ADDED
}
```

- [ ] **Step 3: 前端添加"批量命令"页面入口**

在 `Tasks.vue` 的 createTypeOptions 中添加:
```javascript
{ label: '批量命令', value: 'command' }
```

- [ ] **Step 4: 提交**

Run: `git add ansible/playbooks/run_commands.yml backend/app/models/task_record.py backend/app/services/task_manager.py && git commit -m "feat: add batch command execution task type"`

---

### Task 2.3: 集成测试 + E2E 测试 (P0)

**文件:**
- Create: `backend/tests/test_api_auth.py`
- Create: `backend/tests/test_api_devices.py`
- Create: `backend/tests/test_api_agent.py`

- [ ] **Step 1: 写 API 集成测试**

```python
# tests/test_api_auth.py
def test_login_and_access_device(client, db_session, admin_user):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = resp.json()["access_token"]
    
    resp = client.get("/api/devices", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

def test_unauthorized_access(client):
    resp = client.get("/api/devices")
    assert resp.status_code == 401
```

```python
# tests/test_api_agent.py
def test_agent_tools_endpoint(client):
    resp = client.post("/api/agent/tools/definitions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["data"]["tools"]) >= 10
```

- [ ] **Step 2: 运行测试**

Run: `cd backend && pytest tests/ -v --tb=short`

Expected: 40+ tests, ALL pass

- [ ] **Step 3: 提交**

Run: `git add backend/tests/ && git commit -m "test: add integration tests for API and Agent tool layer"`

---

### Task 2.4: 定时任务 + 审计日志 (P1)

- [ ] **Step 1: APScheduler 定时备份/采集**

Create `backend/app/services/scheduler.py`:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from ..database import SessionLocal
from ..models.device import Device
from ..models.task_record import TaskRecord, TaskType
from .task_manager import execute_task_async

scheduler = BackgroundScheduler()

def backup_all():
    db = SessionLocal()
    try:
        ids = [r[0] for r in db.query(Device.id).all()]
        if ids:
            t = TaskRecord(task_type=TaskType.BACKUP, device_ids=ids)
            db.add(t); db.commit(); db.refresh(t)
            execute_task_async(t.id)
    finally:
        db.close()

def collect_all():
    db = SessionLocal()
    try:
        ids = [r[0] for r in db.query(Device.id).all()]
        if ids:
            t = TaskRecord(task_type=TaskType.COLLECT, device_ids=ids)
            db.add(t); db.commit(); db.refresh(t)
            execute_task_async(t.id)
    finally:
        db.close()

def init_scheduler():
    scheduler.add_job(backup_all, 'cron', hour=2, minute=0, id='daily_backup')
    scheduler.add_job(collect_all, 'interval', hours=4, id='periodic_collect')
    scheduler.start()
```

- [ ] **Step 2: 审计日志服务**

Create `backend/app/services/audit.py` and `backend/app/models/audit_log.py`:
```python
# models/audit_log.py
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False)
    resource = Column(String(64), nullable=False)
    resource_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(39), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 3: 提交**

Run: `git add backend/app/services/scheduler.py backend/app/services/audit.py backend/app/models/audit_log.py backend/requirements.txt && git commit -m "feat: add scheduled tasks and audit logging"`

---

### Phase 2 完成标准

```
✅ AI 智能体可以调用 13 个工具完成网络运维操作
✅ 自然语言指令入口可用
✅ 操作确认工作流 (AI提议→用户确认→执行)
✅ 批量命令执行
✅ 集成测试 40+ 通过
✅ 每日定时备份 + 每4小时性能采集
✅ 用户操作审计日志
```

---

## Phase 3: 资源与报表管理 📋 待开始

### 目标

补全 IP 地址管理、链路管理、巡检报告等 CMNET 日常必备功能。

### Task 3.1: IP 地址管理 (IPAM)

**文件:**
- Create: `backend/app/models/ipam.py`
- Create: `backend/app/routers/ipam.py`
- Create: `backend/app/schemas/ipam.py`
- Create: `frontend/src/views/IPAM.vue`
- Modify: `frontend/src/router/index.js`

- [ ] **Step 1: IPAM 数据模型**

```python
# models/ipam.py
from sqlalchemy import Column, DateTime, Integer, String, Boolean
from sqlalchemy.sql import func
from ..database import Base

class IPSubnet(Base):
    """IP 子网段管理"""
    __tablename__ = "ip_subnets"
    id = Column(Integer, primary_key=True, index=True)
    network = Column(String(18), nullable=False)     # e.g. 10.0.0.0/24
    vlan_id = Column(Integer, nullable=True)
    vrf = Column(String(32), default="default")       # VPN实例
    purpose = Column(String(64), nullable=True)       # 用途: 互联地址/环回地址/管理地址
    location = Column(String(64), nullable=True)      # 武汉/襄阳
    description = Column(String(256), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class IPAddress(Base):
    """IP 地址分配记录"""
    __tablename__ = "ip_addresses"
    id = Column(Integer, primary_key=True, index=True)
    subnet_id = Column(Integer, nullable=False)
    ip_address = Column(String(15), nullable=False)   # 10.0.0.1
    status = Column(String(16), default="used")        # used/available/reserved
    device_id = Column(Integer, nullable=True)          # 分配给哪台设备
    interface = Column(String(32), nullable=True)       # GE0/0/1
    description = Column(String(128), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 2: IPAM API 路由**

```python
# routers/ipam.py
router = APIRouter(prefix="/api/ipam", dependencies=[Depends(get_current_user)])

@router.get("/subnets")
def list_subnets(db: Session = Depends(get_db)):
    return db.query(IPSubnet).all()

@router.post("/subnets")
def create_subnet(data: dict, db: Session = Depends(get_db)):
    subnet = IPSubnet(**data)
    # Auto-generate IP addresses in this subnet
    db.add(subnet)
    db.commit()
    return subnet

@router.get("/addresses")
def list_addresses(subnet_id: int = None, status: str = None, db: Session = Depends(get_db)):
    query = db.query(IPAddress)
    if subnet_id: query = query.filter(IPAddress.subnet_id == subnet_id)
    if status: query = query.filter(IPAddress.status == status)
    return query.all()
```

- [ ] **Step 3: 前端 IPAM 页面**

IP 地址管理界面：左侧子网列表，右侧地址分配可视化表格，支持搜索和过滤。

- [ ] **Step 4: CMNET IP 规划种子数据**

在 `seed.py` 中添加 CMNET 标准 IP 规划：

```python
# CMNET 城域网 IP 规划示例
IP_PLAN = [
    # 互联地址 (Interconnect /30)
    ("10.255.1.0/30", "BB-1 to PB-1", 4091, "互联地址", "武汉"),
    ("10.255.1.4/30", "BB-1 to PB-2", 4092, "互联地址", "武汉"),
    # 环回地址 (Loopback /32)
    ("10.0.0.0/32", "PB-1 Loopback0", None, "环回地址", "武汉"),
    # 管理地址 (Management /24)
    ("192.168.100.0/24", "管理段", None, "管理地址", "武汉"),
    # 业务地址
    ("172.16.1.0/24", "集团专线", 100, "业务地址", "武汉"),
]
```

- [ ] **Step 5: 注册路由和菜单**

```python
# main.py
from .routers.ipam import router as ipam_router
app.include_router(ipam_router)
```

```javascript
// frontend/src/router/index.js
{ path: '/ipam', component: () => import('../views/IPAM.vue') }

// frontend/src/App.vue (菜单)
{ label: 'IP 地址', key: '/ipam', icon: () => h(NIcon, null, { default: () => h(ClusterOutlined) }) }
```

- [ ] **Step 6: 提交**

Run: `git add backend/app/models/ipam.py backend/app/routers/ipam.py backend/app/schemas/ipam.py backend/seed.py frontend/src/views/IPAM.vue frontend/src/router/index.js && git commit -m "feat: add IP address management (IPAM) module"`

---

### Task 3.2: 链路/端口管理

**文件:**
- Create: `backend/app/models/link.py`
- Create: `backend/app/routers/links.py`
- Create: `frontend/src/views/Links.vue`

- [ ] **Step 1: 链路模型**

```python
# models/link.py
class NetworkLink(Base):
    """设备间链路"""
    __tablename__ = "network_links"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)        # PB-1_to_PB-2
    device_a_id = Column(Integer, nullable=False)
    interface_a = Column(String(32), nullable=False)  # GE0/0/1
    device_z_id = Column(Integer, nullable=False)
    interface_z = Column(String(32), nullable=False)  # GE0/0/2
    bandwidth = Column(String(16), default="10GE")    # 带宽
    link_type = Column(String(16), default="trunk")   # trunk/access/routed
    status = Column(String(16), default="up")
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 2: 拓扑图联动链路数据**

修改 `TopologyView.vue` 从 API 获取链路数据（当前是硬编码），实现链路状态颜色变化。

- [ ] **Step 3: 提交**

Run: `git commit -m "feat: add network link management with topology integration"`

---

### Task 3.3: 巡检报告生成 (P1)

**文件:**
- Create: `backend/app/services/report_generator.py`
- Create: `backend/templates/report.html`

- [ ] **Step 1: 报告模板**

使用 Jinja2 生成 HTML 巡检报告，含设备状态、配置备份状态、合规检查结果、性能趋势。

- [ ] **Step 2: 报告 API**

```python
@router.get("/api/reports/daily")
def generate_daily_report(db: Session = Depends(get_db)):
    # 汇总: 设备状态 + 今日任务 + 合规结果 + 性能数据
    # 渲染 HTML → 返回
```

- [ ] **Step 3: 提交**

Run: `git commit -m "feat: add inspection report generation"`

---

### Task 3.4: VLAN 管理 + 软版本管理 (P1)

- [ ] VLAN 管理: 记录 VLAN ID、名称、端口成员
- [ ] 版本管理: 采集并记录设备固件版本、已备份的配置版本列表

---

## Phase 4: 监控与告警 📋 待开始

### 目标

构建告警规则引擎、延迟监控、SLA 统计、报表。

### Task 4.1: 告警规则引擎 + 通知

**文件:**
- Create: `backend/app/models/alert_rule.py`
- Create: `backend/app/services/alerts.py`
- Create: `backend/app/routers/alerts.py`

- [ ] **Step 1: 告警规则模型**

```python
class AlertRule(Base):
    __tablename__ = "alert_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    metric_type = Column(String(32), nullable=False)   # cpu/memory/interface_down
    operator = Column(String(8), nullable=False)       # gt/lt
    threshold = Column(Float, nullable=False)
    enabled = Column(Boolean, default=True)
    notify_channel = Column(String(32), default="webhook")
    notify_target = Column(String(256), nullable=True)
```

- [ ] **Step 2: 告警检查 + 通知**

在 `task_manager.py` 的 `_store_metrics` 中增加告警检查，触发时发送通知。

- [ ] **Step 3: 前端告警规则管理**

CRUD 界面 + 告警历史列表。

- [ ] **Step 4: 提交**

Run: `git commit -m "feat: add alert rules engine and notification"`

---

### Task 4.2: 网络延迟监控 (P2)

- [ ] 使用 Ansible ping/ansible.netcommon 模块采集设备延迟
- [ ] 结果入库并展示趋势图

### Task 4.3: SLA 统计 + 日报 (P2)

- [ ] 计算设备 uptime、配置备份成功率、任务成功率
- [ ] 生成日报/周报 HTML/PDF

---

## Phase 5: 日志与智能运维 📋 远期规划

### 目标

引入 Syslog 接收、故障辅助分析、AI 智能巡检。

### Task 5.1: Syslog 日志接收

- [ ] 集成 syslog-ng 或 rsyslog 接收设备日志
- [ ] 日志入库 + Web 界面查看/搜索
- [ ] 日志与告警关联

### Task 5.2: AI 智能巡检

- [ ] AI Agent 自动执行每日巡检：备份 → 采集 → 合规检查 → 生成报告
- [ ] AI 自动分析合规异常并给出修复建议
- [ ] 自然语言查询："昨天有哪些设备配置发生了变化？"

### Task 5.3: 故障辅助分析

- [ ] 结合 Syslog + Metrics + Config 变更，辅助定位故障
- [ ] AI Agent 给出故障分析建议

---

## 汇总

| 阶段 | 任务 | 预估 | 优先级 |
|------|------|------|--------|
| **Phase 2** | AI 智能体接入层 (Tool Defs + NL + 确认流) | 40min | **P0** |
| | 批量命令执行 | 15min | **P0** |
| | 集成测试 + E2E 测试 | 25min | **P0** |
| | 定时任务 + 审计日志 | 20min | P1 |
| **Phase 3** | IP 地址管理 (IPAM) | 40min | **P0** |
| | 链路管理 | 25min | P1 |
| | 巡检报告 | 20min | P1 |
| | VLAN + 版本管理 | 15min | P1 |
| **Phase 4** | 告警规则引擎 | 25min | P1 |
| | 延迟监控 | 15min | P2 |
| | SLA + 日报 | 20min | P2 |
| **Phase 5** | Syslog 接收 | 30min | P3 |
| | AI 智能巡检 | 30min | P3 |
| | 故障辅助分析 | 20min | P3 |
| | **总计** | **~5.5 小时** | |
