# NetOps CMNET Phase 3 — Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Phase 2 CRUD prototype into a production-ready carrier-grade network operations platform with testing, deployment, monitoring, and operations automation.

**Architecture:** Modular vertical-slice pattern. Each task group is independent — testing adds coverage for existing code, deployment wraps existing code, monitoring alerts sit alongside existing metrics. No major refactoring of working code needed.

**Tech Stack:** pytest + Playwright (testing), Docker + docker-compose (deployment), APScheduler (cron), WebSocket (real-time), Prometheus/AlertManager (alerting), GitHub Actions (CI/CD).

---

## Current Project State (Audit)

### ✅ Completed (Phase 2)

| Domain | Details | Lines |
|--------|---------|-------|
| Backend models | 7 SQLAlchemy models: User, Device, Credential, ConfigArchive, Metric, TaskRecord | 174 |
| Backend routers | 7 CRUD routers: auth, credentials, devices, configs, monitor, tasks, dashboard | 414 |
| Backend services | 6 services: auth(JWT), crypto, ansible_runner, inventory, result_parser, task_manager | 832 |
| Agent API | 10 endpoints with unified response envelope + dual-mode auth (JWT/API-Key) | 374 |
| Frontend views | 7 pages: Login, Dashboard, Devices, Credentials, Config, Monitor, Tasks | 1,166 |
| Frontend components | 3 components: StatCards, TopologyView(SVG), ConfigStatusTable | 257 |
| Ansible | 4 playbooks + inventory builder + result parser | 119 |
| Database | MySQL with connection pooling, auto-create, utf8mb4 | — |
| Auth | JWT Bearer + bcrypt passwords + encrypted credentials | — |

**Total codebase:** ~2,080 Python + 1,593 Vue/JS + 119 YAML = **~3,792 lines**

### ❌ Gaps to Close

| Gap | Severity | Description |
|-----|----------|-------------|
| Testing | **CRITICAL** | Zero tests across entire project |
| Deployment | HIGH | No Docker setup, no docker-compose |
| CI/CD | HIGH | No pipeline, git not initialized |
| Alerting | HIGH | No alert rules or notification system |
| Scheduled tasks | MEDIUM | No periodic backup/compliance automation |
| Audit logging | MEDIUM | No user operation trail |
| User management | MEDIUM | Single admin role, no management UI |
| Real-time updates | MEDIUM | Task progress requires manual polling |
| API hardening | LOW | No rate limiting, inconsistent pagination |
| Code quality | LOW | No linting/formatting config |

---

### Task 1: Testing Infrastructure — Unit Tests

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`
- Create: `backend/tests/test_credentials.py`
- Create: `backend/tests/test_devices.py`
- Create: `backend/tests/test_parsers.py`
- Create: `backend/tests/test_crypto.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Create test configuration and fixtures**

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import create_app

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run pytest to verify fixture works**

Run: `cd backend && pytest tests/ -v`

Expected: No tests collected yet, but conftest loads without ImportError

- [ ] **Step 3: Write auth service tests**

```python
# tests/test_auth.py
import pytest
from app.services.auth import hash_password, verify_password, create_token
from jose import jwt
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM

def test_password_hashing():
    pwd = hash_password("test123")
    assert pwd != "test123"
    assert verify_password("test123", pwd)
    assert not verify_password("wrong", pwd)

def test_token_creation():
    token = create_token(1, "admin")
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert payload["sub"] == "1"
    assert payload["username"] == "admin"
```

- [ ] **Step 4: Write crypto service tests**

```python
# tests/test_crypto.py
from app.services.crypto import encrypt, decrypt

def test_encrypt_decrypt_roundtrip():
    plain = "MySecretPassword123!"
    encrypted = encrypt(plain)
    assert encrypted != plain
    assert decrypt(encrypted) == plain

def test_empty_strings():
    assert encrypt("") == ""
    assert decrypt("") == ""
```

- [ ] **Step 5: Write parser tests**

```python
# tests/test_parsers.py
from app.services.result_parser import parse_cpu, parse_memory, parse_interfaces, check_snmp_compliance

def test_parse_cpu():
    text = "CPU Usage Stats : 45%   last 5 minutes"
    assert parse_cpu(text) == 45.0

def test_parse_cpu_no_match():
    assert parse_cpu("no cpu data here") is None

def test_parse_memory():
    text = "Memory Util. Stat. : 62%  total 8192 MB"
    assert parse_memory(text) == 62.0

def test_parse_interfaces():
    text = "Interface      Status\nGE0/0/1       up\nGE0/0/2       down\nGE0/0/3       up"
    result = parse_interfaces(text)
    assert any(r["type"] == "interface_up" and r["value"] == 2 for r in result)
    assert any(r["type"] == "interface_down" and r["value"] == 1 for r in result)

def test_snmp_compliance_default_community():
    text = "snmp-agent community read public"
    result = check_snmp_compliance(text)
    assert any(r["status"] == "fail" for r in result)
```

- [ ] **Step 6: Write device and credential API tests**

```python
# tests/test_devices.py
from app.models.device import Device, DeviceType, DeviceRole, DeviceStatus

def test_create_device(db_session):
    dev = Device(name="test-device", ip_address="10.0.0.1",
                 device_type=DeviceType.CR, role=DeviceRole.CORE)
    db_session.add(dev)
    db_session.commit()
    assert dev.id is not None
    assert dev.status == DeviceStatus.UNKNOWN  # default

# tests/test_credentials.py
from app.models.credential import Credential, AuthType
from app.services.crypto import encrypt

def test_credential_encryption(db_session):
    cred = Credential(name="test-creds", username="admin",
                      password_encrypted=encrypt("secret123"))
    db_session.add(cred)
    db_session.commit()
    assert cred.id is not None
```

- [ ] **Step 7: Add pytest to requirements**

Append to `backend/requirements.txt`:
```
pytest==8.3.0
httpx==0.27.0
```

- [ ] **Step 8: Run all tests and verify they pass**

Run: `cd backend && pip install pytest httpx && pytest tests/ -v`

Expected: ALL tests PASS

- [ ] **Step 9: Commit**

Run: `git add backend/tests/ backend/requirements.txt && git commit -m "test: add unit tests for services, models, and parsers"`

---

### Task 2: Integration Tests for API Endpoints

**Files:**
- Create: `backend/tests/test_api_auth.py`
- Create: `backend/tests/test_api_devices.py`
- Create: `backend/tests/test_api_credentials.py`
- Create: `backend/tests/test_api_agent.py`

- [ ] **Step 1: Write auth API integration tests**

```python
# tests/test_api_auth.py
from app.models.user import User
from app.services.auth import hash_password

def test_login_success(client, db_session):
    user = User(username="admin", password_hash=hash_password("admin123"), role="admin")
    db_session.add(user)
    db_session.commit()
    
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["username"] == "admin"

def test_login_invalid_password(client, db_session):
    user = User(username="admin", password_hash=hash_password("admin123"), role="admin")
    db_session.add(user)
    db_session.commit()
    
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401

def test_me_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
```

- [ ] **Step 2: Write device API integration tests**

```python
# tests/test_api_devices.py
def test_list_devices(client, db_session):
    from app.models.device import Device, DeviceType, DeviceRole
    db_session.add(Device(name="PB-1", ip_address="10.0.0.1",
                          device_type=DeviceType.PB, role=DeviceRole.CORE))
    db_session.commit()
    
    # First login
    from app.models.user import User
    from app.services.auth import hash_password
    db_session.add(User(username="admin", password_hash=hash_password("admin123"), role="admin"))
    db_session.commit()
    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = client.get("/api/devices", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
```

- [ ] **Step 3: Write Agent API integration tests**

```python
# tests/test_api_agent.py
def test_agent_health_no_auth(client):
    resp = client.get("/api/agent/health")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

def test_agent_devices_requires_auth(client):
    resp = client.get("/api/agent/devices")
    assert resp.status_code == 401
```

- [ ] **Step 4: Run all tests**

Run: `cd backend && pytest tests/ -v`

Expected: ALL tests PASS (target: 20+ tests)

- [ ] **Step 5: Verify coverage meets 80% threshold**

Run: `cd backend && pip install pytest-cov && pytest tests/ --cov=app --cov-report=term-missing`

Expected: Coverage >= 80% for services/, > 50% for routers/

- [ ] **Step 6: Commit**

Run: `git add backend/tests/ && git commit -m "test: add integration tests for API endpoints"`

---

### Task 3: E2E Tests with Playwright

**Files:**
- Create: `frontend/tests/e2e/login.spec.js`
- Create: `frontend/tests/e2e/devices.spec.js`
- Create: `frontend/playwright.config.js`

- [ ] **Step 1: Install Playwright and create config**

Run: `cd frontend && npm install --save-dev @playwright/test && npx playwright install chromium`

Create `frontend/playwright.config.js`:
```javascript
import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests/e2e',
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: true,
  },
})
```

- [ ] **Step 2: Write login E2E test**

```javascript
// tests/e2e/login.spec.js
import { test, expect } from '@playwright/test'

test('login page loads and shows form', async ({ page }) => {
  await page.goto('http://localhost:5173/login')
  await expect(page.locator('text=NetOps')).toBeVisible()
  await expect(page.locator('text=登 录')).toBeVisible()
})
```

- [ ] **Step 3: Write device page E2E test**

```javascript
// tests/e2e/devices.spec.js
test('devices page shows device list after login', async ({ page }) => {
  await page.goto('http://localhost:5173/login')
  await page.fill('input[placeholder="请输入用户名"]', 'admin')
  await page.fill('input[placeholder="请输入密码"]', 'admin123')
  await page.click('text=登 录')
  await page.waitForURL('http://localhost:5173/')
  await page.goto('http://localhost:5173/devices')
  await expect(page.locator('text=设备管理')).toBeVisible()
})
```

- [ ] **Step 4: Run E2E tests**

Run: Ensure backend is running on :8000, then: `cd frontend && npx playwright test`

Expected: Both tests PASS

- [ ] **Step 5: Commit**

Run: `git add frontend/tests/ frontend/playwright.config.js frontend/package.json && git commit -m "test: add Playwright E2E tests for login and devices"`

---

### Task 4: Docker Deployment

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `nginx/default.conf`

- [ ] **Step 1: Create backend Dockerfile**

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create frontend Dockerfile**

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY ../nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 3: Create docker-compose.yml**

```yaml
# docker-compose.yml
version: "3.8"
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: netops_cmnet
      MYSQL_USER: netops
      MYSQL_PASSWORD: netops123
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: mysql+pymysql://netops:netops123@mysql:3306/netops_cmnet?charset=utf8mb4
      JWT_SECRET_KEY: change-in-production
      AGENT_API_KEY: cmnet-agent-key-2026
    depends_on:
      - mysql
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    depends_on:
      - backend
    ports:
      - "80:80"

volumes:
  mysql_data:
```

- [ ] **Step 4: Create nginx config**

```nginx
# nginx/default.conf
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] **Step 5: Build and verify Docker setup**

Run: `docker-compose build && docker-compose up -d`

Expected: All containers start, health check returns 200

- [ ] **Step 6: Commit**

Run: `git add docker-compose.yml Dockerfile backend/Dockerfile frontend/Dockerfile nginx/ .dockerignore && git commit -m "deploy: add Docker deployment with docker-compose"`

---

### Task 5: CI/CD Pipeline (GitHub Actions)

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Create CI workflow**

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root123
          MYSQL_DATABASE: netops_cmnet
          MYSQL_USER: netops
          MYSQL_PASSWORD: netops123
        ports: ["3306:3306"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: cd backend && pip install -r requirements.txt pytest pytest-cov httpx
      - run: cd backend && pytest tests/ --cov=app --cov-report=term-missing
      - run: cd backend && coverage report --fail-under=80

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: cd frontend && npm ci
      - run: cd frontend && npx playwright install chromium
      - run: cd frontend && npx playwright test
```

- [ ] **Step 2: Initialize git and push**

Run: `cd /c/Users/CMCC/netops-cmnet && git init && git add -A && git commit -m "feat: initial NetOps CMNET platform"`

- [ ] **Step 3: Commit CI config**

Run: `git add .github/ && git commit -m "ci: add GitHub Actions CI pipeline"`

---

### Task 6: Scheduled Tasks with APScheduler

**Files:**
- Modify: `backend/app/config.py`
- Create: `backend/app/services/scheduler.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Add APScheduler to requirements**

Add to `backend/requirements.txt`:
```
apscheduler==3.10.4
```

- [ ] **Step 2: Create scheduler service**

```python
# backend/app/services/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from ..database import SessionLocal
from ..models.device import Device
from ..models.task_record import TaskRecord, TaskType
from .task_manager import execute_task_async

scheduler = BackgroundScheduler()
BACKUP_CRON = os.getenv("BACKUP_CRON", "0 2 * * *")      # daily 2am
COLLECT_CRON = os.getenv("COLLECT_CRON", "0 */4 * * *")   # every 4 hours

def backup_all_devices():
    db = SessionLocal()
    try:
        device_ids = [r[0] for r in db.query(Device.id).all()]
        if device_ids:
            task = TaskRecord(task_type=TaskType.BACKUP, device_ids=device_ids)
            db.add(task)
            db.commit()
            db.refresh(task)
            execute_task_async(task.id)
    finally:
        db.close()

def collect_all_metrics():
    db = SessionLocal()
    try:
        device_ids = [r[0] for r in db.query(Device.id).all()]
        if device_ids:
            task = TaskRecord(task_type=TaskType.COLLECT, device_ids=device_ids)
            db.add(task)
            db.commit()
            db.refresh(task)
            execute_task_async(task.id)
    finally:
        db.close()

def init_scheduler():
    scheduler.add_job(backup_all_devices, 'cron', hour=2, minute=0, id='daily_backup')
    scheduler.add_job(collect_all_metrics, 'interval', hours=4, id='periodic_collect')
    scheduler.start()
```

- [ ] **Step 3: Register scheduler in main.py**

```python
# In main.py create_app()
from .services.scheduler import init_scheduler

@app.on_event("startup")
def on_start() -> None:
    init_db()
    init_scheduler()
```

- [ ] **Step 4: Test scheduler loads without error**

Run: `cd backend && .venv/Scripts/python -c "from app.services.scheduler import init_scheduler; print('scheduler OK')"`

Expected: Prints "scheduler OK"

- [ ] **Step 5: Commit**

Run: `git add backend/requirements.txt backend/app/services/scheduler.py backend/app/main.py && git commit -m "feat: add APScheduler for periodic backup and metrics collection"`

---

### Task 7: Audit Logging System

**Files:**
- Create: `backend/app/models/audit_log.py`
- Create: `backend/app/services/audit.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create audit log model**

```python
# backend/app/models/audit_log.py
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func
from ..database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False)      # create/update/delete/login
    resource = Column(String(64), nullable=False)     # device/credential/task/config
    resource_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(39), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 2: Create audit service**

```python
# backend/app/services/audit.py
from ..database import SessionLocal
from ..models.audit_log import AuditLog

def log_action(user_id: int | None, username: str | None, action: str,
               resource: str, resource_id: int | None = None,
               detail: str | None = None, ip_address: str | None = None) -> None:
    db = SessionLocal()
    try:
        db.add(AuditLog(
            user_id=user_id, username=username, action=action,
            resource=resource, resource_id=resource_id,
            detail=detail, ip_address=ip_address,
        ))
        db.commit()
    finally:
        db.close()
```

- [ ] **Step 3: Integrate audit into credential and device routers**

In `routers/credentials.py`, after create/update/delete:
```python
from ..services.audit import log_action
# In create_credential:
log_action(current_user.id, current_user.username, "create", "credential", cred.id)
```

- [ ] **Step 4: Commit**

Run: `git add backend/app/models/audit_log.py backend/app/services/audit.py backend/app/models/__init__.py && git commit -m "feat: add audit logging for user operations"`

---

### Task 8: WebSocket Real-Time Updates

**Files:**
- Create: `backend/app/routers/ws.py`
- Modify: `backend/app/main.py`
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: Create WebSocket endpoint**

```python
# backend/app/routers/ws.py
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.auth import get_current_user_ws

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []
    
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
    
    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
    
    async def broadcast(self, message: dict):
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/ws/tasks")
async def task_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

- [ ] **Step 2: Register WebSocket router in main.py**

```python
from .routers.ws import router as ws_router
app.include_router(ws_router)
```

- [ ] **Step 3: Add WebSocket client in frontend**

In `frontend/src/api/index.js`:
```javascript
export function connectTaskWebSocket(onMessage) {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${location.host}/ws/tasks`)
  ws.onmessage = (event) => onMessage(JSON.parse(event.data))
  return ws
}
```

- [ ] **Step 4: Integrate broadcast into task_manager.py**

In `task_manager.py`, after task completion:
```python
import asyncio
from .routers.ws import manager
# After task finishes:
asyncio.run(manager.broadcast({
    "type": "task_update",
    "task_id": task.id,
    "status": task.status,
}))
```

- [ ] **Step 5: Commit**

Run: `git add backend/app/routers/ws.py backend/app/main.py frontend/src/api/index.js && git commit -m "feat: add WebSocket real-time task updates"`

---

### Task 9: API Response Standardization

**Files:**
- Modify: `backend/app/routers/devices.py` (list_devices response_model)
- Modify: `backend/app/routers/configs.py` (response_model)
- Modify: `backend/app/routers/monitor.py` (response_model)
- Modify: `backend/app/routers/tasks.py` (response_model)

- [ ] **Step 1: Add missing Pydantic response schemas**

```python
# backend/app/schemas/config.py
from datetime import datetime
from pydantic import BaseModel

class ConfigResponse(BaseModel):
    id: int
    device_id: int
    version: str
    content: str
    diff_previous: str | None
    collected_at: datetime
    model_config = {"from_attributes": True}

class ConfigDiffResponse(BaseModel):
    old_version: str
    new_version: str
    diff: str | None
```

- [ ] **Step 2: Add response_model to list_devices**

```python
@router.get("", response_model=dict)
def list_devices(...):
    # Already returns {"total": N, "items": [...]} — wrap DeviceResponse
    return {"total": total, "items": [_device_to_dict(d) for d in devices]}
```

- [ ] **Step 3: Add response_model to config endpoints**

```python
@router.get("/{device_id}", response_model=list[ConfigResponse])
```

- [ ] **Step 4: Add response_model to task endpoints**

```python
@router.get("", response_model=dict)
```

- [ ] **Step 5: Commit**

Run: `git add backend/app/schemas/config.py backend/app/routers/ && git commit -m "refactor: standardize API response models for all endpoints"`

---

### Task 10: Alert Rules and Notifications

**Files:**
- Create: `backend/app/services/alerts.py`
- Create: `backend/app/routers/alerts.py`
- Create: `backend/app/models/alert_rule.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create alert rule model**

```python
# backend/app/models/alert_rule.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from ..database import Base

class AlertRule(Base):
    __tablename__ = "alert_rules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    metric_type = Column(String(32), nullable=False)   # cpu/memory/interface_down
    operator = Column(String(8), nullable=False)       # gt/lt
    threshold = Column(Float, nullable=False)
    enabled = Column(Boolean, default=True)
    notify_channel = Column(String(32), default="webhook")  # email/webhook/sms
    notify_target = Column(String(256), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 2: Create alert checker service**

```python
# backend/app/services/alerts.py
def check_metric_alert(device_id: int, metric_type: str, value: float) -> list[dict]:
    """Check metric value against all enabled rules. Returns triggered alerts."""
    db = SessionLocal()
    try:
        rules = db.query(AlertRule).filter(
            AlertRule.metric_type == metric_type,
            AlertRule.enabled == True,
        ).all()
        triggered = []
        for rule in rules:
            is_triggered = (
                (rule.operator == "gt" and value > rule.threshold) or
                (rule.operator == "lt" and value < rule.threshold)
            )
            if is_triggered:
                triggered.append({"rule": rule.name, "metric": value, "threshold": rule.threshold})
        return triggered
    finally:
        db.close()
```

- [ ] **Step 3: Create alert CRUD router**

```python
# backend/app/routers/alerts.py
router = APIRouter(prefix="/api/alerts", dependencies=[Depends(get_current_user)])

@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    return db.query(AlertRule).all()

@router.post("/rules")
def create_rule(data: dict, db: Session = Depends(get_db)):
    rule = AlertRule(**data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
```

- [ ] **Step 4: Register alert router**

In `main.py`:
```python
from .routers.alerts import router as alerts_router
app.include_router(alerts_router)
```

- [ ] **Step 5: Commit**

Run: `git add backend/app/models/alert_rule.py backend/app/services/alerts.py backend/app/routers/alerts.py backend/app/main.py && git commit -m "feat: add alert rules engine and notification support"`

---

## Summary

| Task | Priority | Files | Est. Time |
|------|----------|-------|-----------|
| 1. Unit Tests | CRITICAL | 8 new | 25 min |
| 2. Integration Tests | CRITICAL | 4 new | 20 min |
| 3. E2E Tests | HIGH | 3 new | 15 min |
| 4. Docker Deployment | HIGH | 5 new | 20 min |
| 5. CI/CD Pipeline | HIGH | 2 new | 15 min |
| 6. Scheduled Tasks | MEDIUM | 1 new, 2 modify | 15 min |
| 7. Audit Logging | MEDIUM | 2 new, 1 modify | 15 min |
| 8. WebSocket | MEDIUM | 1 new, 2 modify | 20 min |
| 9. API Standardization | LOW | 1 new, 4 modify | 15 min |
| 10. Alert Rules | MEDIUM | 3 new, 1 modify | 20 min |
| **Total** | | **30+ files** | **~3 hours** |
