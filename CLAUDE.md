# NetOps CMNET

Network operations management platform for CMNET (China Mobile Network) carrier-grade network. Manages Huawei CE CloudEngine series devices across a provincial network topology.

## Architecture

```
netops-cmnet/
├── backend/           # Python FastAPI backend
│   ├── app/
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── routers/   # API route handlers
│   │   ├── schemas/   # Pydantic request/response schemas
│   │   └── services/  # Business logic (Ansible, crypto, parsing)
│   ├── seed.py        # Database seeder with 19 devices
│   └── requirements.txt
├── frontend/          # Vue 3 + Naive UI SPA
│   ├── src/
│   │   ├── views/     # 6 page views (Dashboard, Devices, Config, Monitor, Credentials, Tasks)
│   │   ├── components/# Reusable components (StatCards, TopologyView, ConfigStatusTable)
│   │   ├── api/       # Axios API client
│   │   └── router/    # Vue Router config
│   └── vite.config.js # Vite dev server proxies /api to :8000
└── ansible/           # Ansible playbooks for Huawei CE
    ├── playbooks/     # backup, collect_metrics, compliance_check, push_config
    └── ansible.cfg
```

## Network Topology

- **BB** (集团骨干): BB-1, BB-2
- **PB** (省网核心): PB-1, PB-2
- **MB** (城域核心): A_MB_1, A_MB_2 (武汉), B_MB_1, B_MB_2 (襄阳)
- **BRAS** (业务接入): A-BRAS (武汉), B-BRAS (襄阳)
- **RR** (路由反射): VPN_RR-1, VPN_RR-2
- **PE** (客户边缘): C-1, C-2
- **PC** (自有业务): PC-1 (武汉), PC-2 (襄阳)
- **SW** (管理): S-1, S-3, S-5

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
python seed.py  # Creates admin user + 19 devices
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # starts on :5173, proxies /api to :8000
```

### Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

## API Endpoints

| Prefix | Auth | Description |
|--------|------|-------------|
| `/api/auth/login` | No (public) | JWT login |
| `/api/auth/me` | Yes | Current user info |
| `/api/health` | No (public) | Health check |
| `/api/credentials` | Yes | SSH credential CRUD |
| `/api/devices` | Yes | Device inventory CRUD |
| `/api/configs` | Yes | Config archive retrieval & diff |
| `/api/monitor` | Yes | Performance metrics (CPU, memory, interface) |
| `/api/tasks` | Yes | Ansible task management |
| `/api/dashboard` | Yes | Stats, device-type distribution, recent tasks |

## Auth Flow

- JWT-based stateless auth with `passlib[bcrypt]` password hashing
- Token stored in `localStorage`, sent as `Authorization: Bearer <token>`
- Token expires after 480 minutes (configurable via `JWT_EXPIRE_MINUTES` env)
- Frontend route guard redirects to `/login` when unauthenticated

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite, Pydantic, python-jose (JWT), passlib (bcrypt)
- **Frontend**: Vue 3, Naive UI, ECharts, Vue Router, Axios, Vite
- **Automation**: Ansible, community.network collection (Huawei CE)

## Current State

Phase 2 — Core CRUD + Auth + Ansible task management. JWT authentication implemented for all API routes except `/api/auth/login` and `/api/health`.
