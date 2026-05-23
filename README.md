# NetOps CCC

网络运维管理平台，面向网络场景。通过 Ansible 自动化管理华为 CE CloudEngine 系列设备，提供 Vue 3 Web UI 和 AI Agent 接口。

## 功能概览

| 模块 | 功能 |
|------|------|
| Dashboard | 全网概览、设备在线率、SLA、拓扑视图 |
| 设备管理 | 设备清单、固件版本、在线状态 |
| 配置管理 | 配置归档、历史版本对比、合规检查 |
| 监控采集 | CPU/内存/接口性能指标、TCP Ping |
| 任务系统 | 备份、采集、合规、配置下发、命令执行 |
| IPAM | IP 地址段管理 |
| 链路管理 | 网络链路拓扑 |
| VLAN 管理 | VLAN 资源管理 |
| 告警引擎 | 告警规则 + 历史告警 |
| Syslog | Syslog 日志查看 |
| AI 巡检 | AI 智能巡检、故障分析 |
| AI Agent | 13 个工具接口，支持 Claude/GPT 调用 |

## 快速开始

### 后端

```bash
cd backend
source .venv/Scripts/activate     # Windows
# source .venv/bin/activate        # Linux
uvicorn app.main:app --reload --port 8000
```

### 初始化数据

```bash
python seed.py    # 创建 admin 用户 + 21 台设备 + 凭证
```

### 前端

```bash
cd frontend
npm install
npm run dev       # 开发模式 :5173
npm run build     # 生产构建 → dist/
```

### 默认账号

| 项目 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `admin123` |
| Agent API Key | `cmnet-agent-key-2026` |

## 技术栈

**后端：** FastAPI · SQLAlchemy · MySQL · Pydantic · JWT · APScheduler  
**前端：** Vue 3 · Naive UI · ECharts · Vue Router · Axios · Vite  
**自动化：** Ansible · community.network (Huawei CE) · Paramiko  
**AI：** Claude/GPT Tool Use · 自然语言接口 · 故障分析引擎

## 项目结构

```
netops-cmnet/
├── backend/
│   ├── app/
│   │   ├── models/       # 15 个 SQLAlchemy 模型
│   │   ├── routers/      # 15 个 API 路由
│   │   ├── schemas/      # Pydantic 请求/响应模型
│   │   └── services/     # 13 个业务逻辑模块
│   ├── seed.py           # 数据初始化
│   ├── requirements.txt
│   └── tests/            # 43 个测试用例
├── frontend/
│   ├── src/
│   │   ├── views/        # 11 个页面
│   │   ├── components/   # 通用组件
│   │   ├── api/          # Axios API 封装
│   │   └── router/       # 路由守卫
│   └── vite.config.js
├── ansible/
│   └── playbooks/        # 5 个 Ansible 剧本
└── deploy/               # 部署脚本
```

## API 接口

| 路径 | 说明 |
|------|------|
| `/api/auth` | 登录认证 (JWT) |
| `/api/devices` | 设备管理 |
| `/api/credentials` | SSH 凭证管理 (加密存储) |
| `/api/configs` | 配置归档与对比 |
| `/api/monitor` | 性能监控 |
| `/api/tasks` | Ansible 任务管理 |
| `/api/dashboard` | 统计概览 |
| `/api/ipam` | IP 地址管理 |
| `/api/links` | 链路管理 |
| `/api/vlans` | VLAN 管理 |
| `/api/alerts` | 告警规则与历史 |
| `/api/syslog` | Syslog 日志 |
| `/api/inspection` | AI 巡检与故障分析 |
| `/api/agent` | AI Agent (13 个工具) |
| `/api/agent/chat` | AI 自然语言入口 |

## AI Agent

平台暴露 13 个工具接口，兼容 OpenAI Function Calling 格式，支持 Claude、GPT 等 AI 模型调用：

- `network_status` / `list_devices` / `diagnose_device` — 查询
- `backup_all_devices` / `compliance_all_devices` — 批量操作
- `run_commands` / `full_inspection` — 执行与巡检

## 部署

```bash
cd deploy
sudo bash deploy.sh    # 一键部署 (Ubuntu + MySQL + Nginx)
```

详细部署文档见 `deploy/` 目录。

## 测试

```bash
cd backend
.venv/Scripts/pytest tests/ -v    # 43 tests, all passing
```
