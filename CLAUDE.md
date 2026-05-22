# NetOps CMNET

Network operations management platform for CMNET (China Mobile Network) carrier-grade network. Manages Huawei CE CloudEngine series devices across a provincial network topology via Ansible automation, with a Vue 3 web UI and AI Agent interface.

## Architecture

```
Windows (开发) / Ubuntu (部署)
├── Frontend/       # Vue 3 + Naive UI SPA (11 pages)
│   ├── views/      # Dashboard, Devices, Config, Monitor, Credentials, Tasks
│   │               # IPAM, Links, Alerts, Syslog, Login
│   ├── components/ # StatCards, TopologyView(SVG), ConfigStatusTable
│   ├── api/        # Axios API client
│   └── router/     # Vue Router with JWT auth guard
├── Backend/        # FastAPI Python (15 models + 15 routers + 13 services)
│   ├── models/     # SQLAlchemy ORM (20+ tables)
│   ├── routers/    # API route handlers
│   ├── schemas/    # Pydantic request/response schemas
│   └── services/   # Business logic (auth, Ansible, crypto, alerts, etc.)
└── Ansible/        # 5 playbooks for Huawei CE
    ├── playbooks/  # backup, collect_metrics, compliance_check, push_config, run_commands
    └── ansible.cfg
```

## Network Topology (eNSP Simulation)

| Layer | Devices | Description |
|-------|---------|-------------|
| BB (骨干) | BB-1, BB-2 | 集团骨干 |
| PB (核心) | PB-1, PB-2 | 省网核心 |
| RR (路由反射) | VPN_RR-1, VPN_RR-2 | VPN路由反射器 |
| MB (城域) | A_MB_1, A_MB_2 (武汉), B_MB_1, B_MB_2 (襄阳) | 城域核心 |
| BRAS (接入) | A-BRAS (武汉), B-BRAS (襄阳) | 业务接入 |
| PE/PC (客户) | C-1, C-2, PC-1, PC-2 | 客户边缘 + 自有业务 |
| SW (管理) | S-1, S-3, S-5, S-11, S-12 | 管理交换机 |

Total: 21 devices, credentials: Rfvbgt#123 / Chasdfgh_666, enable: qwer1234 (S系列)

## Quick Start

### Backend
```bash
cd backend
source .venv/Scripts/activate  # or .venv/bin/activate on Linux
uvicorn app.main:app --reload --port 8000
```

### Seed Data
```bash
cd backend
python seed.py  # Creates admin user + 21 devices + 1 credential
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # :5173, proxies /api to :8000
npm run build  # production build to dist/
```

### Default Credentials
- **Username**: `admin` / **Password**: `admin123`
- **Agent API Key**: `cmnet-agent-key-2026`

## API Endpoints (27+ routes)

| Prefix | Type | Auth | Description |
|--------|------|------|-------------|
| `/api/auth` | REST | JWT | Login, current user |
| `/api/credentials` | CRUD | JWT/API-Key | SSH credential management (encrypted) |
| `/api/devices` | CRUD | JWT/API-Key | Device inventory + firmware versions |
| `/api/configs` | Query | JWT/API-Key | Config archive retrieval & diff |
| `/api/monitor` | Query | JWT/API-Key | Performance metrics, TCP ping |
| `/api/tasks` | CRUD | JWT/API-Key | Ansible task management |
| `/api/dashboard` | Query | JWT/API-Key | Stats, SLA, device-type, report |
| `/api/ipam` | CRUD | JWT/API-Key | IP address management |
| `/api/links` | CRUD | JWT/API-Key | Network link management |
| `/api/vlans` | CRUD | JWT/API-Key | VLAN management |
| `/api/alerts` | CRUD+Query | JWT/API-Key | Alert rules + history |
| `/api/syslog` | Query | JWT/API-Key | Syslog log viewer |
| `/api/inspection` | Exec+Query | JWT/API-Key | AI inspection, fault analysis |
| `/api/agent` | Agent API | JWT/API-Key | AI Agent tool layer (13 tools) |
| `/api/agent/chat` | NL | JWT/API-Key | Natural language agent entry |
| `/api/health` | Public | None | Health check |

### Agent API Tool Definitions (13 tools)

```
network_status   list_devices     diagnose_device    backup_device
backup_all       compliance_check compliance_all     get_task_result
run_commands     get_device_config compare_config    get_metrics
full_inspection
```

All tools return unified `{success, data, error, meta}` format. Compatible with OpenAI Function Calling and Claude Tool Use.

## Auth Flow

- JWT stateless auth with `passlib[bcrypt]` password hashing
- Dual-mode auth: JWT Bearer token OR X-API-Key header
- Agent API supports both modes (frontend uses JWT, AI agents use API-Key)
- Token: 480 min expiry, stored in localStorage, sent as `Authorization: Bearer <token>`

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, MySQL, Pydantic, python-jose (JWT), passlib (bcrypt), APScheduler
- **Frontend**: Vue 3, Naive UI, ECharts, Vue Router, Axios, Vite
- **Automation**: Ansible, community.network collection (Huawei CE), paramiko
- **AI**: Tool-use definitions for Claude/GPT, natural language interface, fault analysis engine

## Project Structure

```
netops-cmnet/
├── backend/
│   ├── app/
│   │   ├── models/       # 15 SQLAlchemy models
│   │   │   ├── device.py, credential.py, user.py
│   │   │   ├── config_archive.py, task_record.py, metric.py
│   │   │   ├── agent_session.py, audit_log.py
│   │   │   ├── ipam.py, link.py, vlan.py, firmware.py
│   │   │   ├── alert_rule.py, syslog.py
│   │   ├── routers/      # 15 route handlers
│   │   │   ├── auth.py, credentials.py, devices.py, configs.py
│   │   │   ├── monitor.py, tasks.py, dashboard.py
│   │   │   ├── agent.py, agent_chat.py
│   │   │   ├── ipam.py, links.py, vlans.py
│   │   │   ├── alerts.py, syslog_viewer.py, phase5.py
│   │   ├── schemas/      # Pydantic models
│   │   ├── services/     # 13 business logic modules
│   │   │   ├── auth.py (JWT), crypto.py (Fernet)
│   │   │   ├── ansible_runner.py, inventory.py
│   │   │   ├── result_parser.py, task_manager.py
│   │   │   ├── agent_tools.py, scheduler.py
│   │   │   ├── audit.py, alerts.py, report_generator.py
│   │   │   ├── ai_inspection.py, fault_analysis.py
│   │   │   ├── syslog_server.py (UDP syslog receiver)
│   ├── seed.py           # Database seeder (21 devices)
│   ├── requirements.txt
│   └── tests/            # 43 tests, all passing
├── frontend/
│   ├── src/
│   │   ├── views/        # 11 pages
│   │   ├── components/   # 3 reusable components
│   │   ├── api/          # Axios client
│   │   └── router/       # Vue Router
│   └── vite.config.js
├── ansible/
│   ├── playbooks/        # 5 playbooks
│   └── ansible.cfg
└── deploy/               # Deployment package
    ├── deploy.sh         # One-click install script
    ├── netops-cmnet.service  # systemd unit
    └── nginx/default.conf    # nginx config
```

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Ansible integration + CRUD + Web UI + Auth + Agent API | ✅ Complete |
| **Phase 2** | AI Agent tool layer + batch commands + scheduler + audit + tests | ✅ Complete |
| **Phase 3** | IPAM + Link management + VLAN + firmware + inspection report | ✅ Complete |
| **Phase 4** | Alert rules engine + SLA + latency check + report enhancement | ✅ Complete |
| **Phase 5** | Syslog receiver + AI inspection + fault analysis | ✅ Complete |

## Deployment

### Ubuntu Production (WSL2 or native)

```bash
# One-click install
cd deploy/
sudo bash deploy.sh
# 自动安装: Python3, MySQL, Nginx, Python 依赖, 种子数据
# 服务: nginx (:80) + netops-cmnet (systemd, :8000)

# Access
#  Web UI: http://<server-ip>
#  API:   http://<server-ip>:8000/docs
```

### Manual Management

```bash
# Backend logs
journalctl -u netops-cmnet -n 50 -f

# Restart
systemctl restart netops-cmnet

# Update code
cd /opt/netops && git pull && systemctl restart netops-cmnet
```

## Deployment Architecture (Production)

```
Ubuntu Server
┌────────────────────────────────────────────┐
│  Nginx (:80)                               │
│  ├── / → frontend/dist (static files)      │
│  └── /api/ → proxy_pass :8000              │
│                                            │
│  netops-cmnet service (:8000)              │
│  ├── FastAPI app (uvicorn, 2 workers)      │
│  ├── Ansible (local subprocess)            │
│  └── Syslog Server (UDP :514)              │
│                                            │
│  MySQL (:3306)                             │
│  └── netops_cmnet database                 │
└────────────────────┬───────────────────────┘
                     │ SSH (jump host)
         ┌───────────▼───────────┐
         │ eNSP Simulator        │
         │ 192.168.10.211        │
         │ Huawei CE (21 devices)│
         │ 192.168.100.0/24     │
         └───────────────────────┘
```

## AI Agent Integration

The platform exposes 13 tools via `/api/agent/tools/definitions` in OpenAI Function Calling format. AI agents (Claude, GPT) can:

1. **Discover** tools via `GET /api/agent/tools/definitions`
2. **Execute** tools via `POST /api/agent/tools/execute`
3. **Chat** via `POST /api/agent/chat` (natural language → tool mapping)

Key tools for network operations:
- `network_status` / `list_devices` / `diagnose_device` — Query
- `backup_all_devices` / `compliance_all_devices` — Batch operations
- `run_commands` — CLI command execution
- `full_inspection` — Combined backup + collect + compliance

## Testing

```bash
cd backend
.venv/Scripts/pytest tests/ -v  # 43 tests, all passing
```
