# NetOps CMNET — 多阶段开发路线图

> **项目目标:** 基于 Ansible + Web UI + AI Agent，实现对 eNSP 华为模拟器内 CMNET 城域网设备的运维管理仿真，最终通过 AI 智能体完成网络设备运维操作。

**架构定位:** Ansible (执行引擎) + 自研层 (业务逻辑/AI接入) + 开源组件 (监控/日志/IPAM)

**参考平台:** 华为 eSight、SolarWinds NPM、Zabbix、锐捷 RIIL

---

## 总体进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| **Phase 1: 基础框架** | Ansible整合 + CRUD + Web UI + Auth | ✅ **已完成** |
| **Phase 2: AI + 运维增强** | AI Agent接入层 + 批量命令 + 定时任务 + 测试 | ✅ **已完成** |
| **Phase 3: 资源与报表** | IPAM + 链路管理 + 巡检报告 + VLAN | ✅ **已完成** |
| **Phase 4: 监控与告警** | 告警引擎 + 延迟监控 + SLA + 报表 | ✅ **已完成** |
| **Phase 5: 日志与智能** | Syslog接收 + 故障辅助 + 智能巡检 | ✅ **已完成** |
| **验收测试** | Ubuntu部署 + eNSP对接验证 | 🔄 **进行中** |

---

## Phase 1: 基础框架 ✅

| 功能 | 状态 |
|------|------|
| Ansible 5 个 Playbook (备份/采集/合规/下发/批量命令) | ✅ |
| 设备台账 CRUD、凭据管理 (Fernet 加密) | ✅ |
| 设备拓扑 (SVG 可视化，21台设备) | ✅ |
| CPU/内存/接口性能采集 (Ansible) | ✅ |
| 性能趋势图表 (ECharts) | ✅ |
| JWT 认证 + bcrypt 密码 + 双模认证 (JWT/API-Key) | ✅ |
| Agent API (10端点 + 统一响应格式) | ✅ |
| 单元测试 (43 tests passing) | ✅ |
| Git 初始化 + MySQL 数据库 | ✅ |

---

## Phase 2: AI + 运维增强 ✅

| 功能 | 状态 |
|------|------|
| AI Agent Tool Definitions (13 tools, OpenAI Function Calling 格式) | ✅ |
| 自然语言指令入口 `/api/agent/chat` | ✅ |
| 操作确认工作流 (AgentSession 模型) | ✅ |
| 批量命令执行 `run_commands.yml` + COMMAND 任务类型 | ✅ |
| APScheduler 定时备份 (每日2点) + 周期采集 (每4小时) | ✅ |
| 审计日志 (AuditLog 模型 + log_action 服务) | ✅ |
| 集成测试 (9 个 Agent API 测试) | ✅ |

---

## Phase 3: 资源与报表 ✅

| 功能 | 状态 |
|------|------|
| IP 地址管理 (IPAM): 子网创建/删除、地址池自动生成、分配/预留/释放 | ✅ |
| 链路/端口管理: CRUD + 带宽/类型/状态 | ✅ |
| VLAN 管理: VLAN ID 规划、名称/用途/位置 | ✅ |
| 固件版本管理: 设备 VRP 版本记录 | ✅ |
| HTML 巡检报告: 设备状态 + CPU + 任务统计 | ✅ |
| 前端页面: IPAM + Links 页面 + 菜单集成 | ✅ |

---

## Phase 4: 监控与告警 ✅

| 功能 | 状态 |
|------|------|
| 告警规则引擎: 指标阈值规则 CRUD (CPU/内存/接口) | ✅ |
| 告警自动触发: 采集指标时自动比对规则、生成告警历史 | ✅ |
| 告警历史: 列表 + 状态管理 (活跃/已解决) + 级别过滤 | ✅ |
| TCP Ping: 设备端口连通性检测 | ✅ |
| SLA 统计: 任务成功率、设备在线率 | ✅ |
| 前端告警页面: 规则管理 + 告警历史标签页 | ✅ |

---

## Phase 5: 日志与智能 ✅

| 功能 | 状态 |
|------|------|
| Syslog UDP 接收服务器 (RFC 3164/5424 解析) | ✅ |
| Syslog 入库 + Web 查询/过滤/汇总 | ✅ |
| AI 智能巡检: 一键全量检查 + 分析报告生成 | ✅ |
| 故障辅助分析: 关联 Syslog + Metrics + 配置变更 + 任务历史 | ✅ |
| 前端 Syslog 页面: 按级别/主机/关键字搜索 | ✅ |

---

## 部署环境

| 组件 | 地址 | 说明 |
|------|------|------|
| **Ubuntu (WSL2)** | `172.25.47.229` | Ansible + NetOps 后端 + MySQL + Nginx |
| **eNSP 模拟器** | `192.168.10.211` | 华为 CE 设备仿真 (21台) |
| **Web UI** | `http://172.25.47.229` | Vue 前端 (Nginx 托管) |
| **API 文档** | `http://172.25.47.229:8000/docs` | FastAPI Swagger |
| **Agent API** | `http://172.25.47.229:8000/api/agent` | AI Agent 接口 |

### 部署方式

```bash
# Ubuntu 一键部署
sudo bash /home/cmcc/netops-deploy/deploy.sh

# 后端管理
systemctl status netops-cmnet   # 检查状态
journalctl -u netops-cmnet -f   # 查看日志
systemctl restart netops-cmnet  # 重启
```

---

## 验收测试 🔄 进行中

### 当前状态

| 项目 | 状态 | 说明 |
|------|------|------|
| Ubuntu 部署 | ✅ 完成 | 系统服务运行正常 |
| API 健康检查 | ✅ 通过 | `/api/agent/health` 返回 OK |
| 数据库验证 | ✅ 通过 | 21 台设备 + 1 admin 用户 |
| Ansible 安装 | ✅ 完成 | ansible-core 2.16.3 |
| 跳板机 SSH | ✅ 通过 | Ubuntu → eNSP 服务器 (192.168.10.211) |
| eNSP 设备 Ping | ✅ 通过 | Ubuntu → 设备 (192.168.100.x) 可达 |
| 凭据加密同步 | ✅ 完成 | Windows ↔ Ubuntu 密钥一致，密码解密正常 |
| SSH 到 eNSP 设备 | ❌ **阻塞** | eNSP 华为 CE 有首次登录密码修改策略 |

### 阻塞问题: eNSP 设备密码策略

**现象:** 华为 CE 设备首次 SSH 登录时要求修改密码:
```
Warning: The initial password poses security risks.
The password needs to be changed, Continue? [Y/N]:
```

**已尝试的方案:**
1. 发送 `N` → 设备拒绝连接
2. 发送 `Y` → 要求输入新旧密码；但新密码不能与旧密码相同
3. 使用 `expect` 自动化密码修改 → 旧密码 `Chasdfgh_666` → 新密码需不同 (如 `Admin@123`)

**待解决:**
- [ ] 使用 expect 脚本为所有 21 台设备执行首次密码修改
- [ ] 或通过 eNSP 控制台/Console 口配置 `undo password-receiver enable` 跳过策略
- [ ] 密码修改后更新数据库凭据、验证 Ansible 备份任务

### 已知配置

| 参数 | 值 |
|------|-----|
| 设备用户名 | `Rfvbgt#123` |
| 设备密码 | `Chasdfgh_666` |
| S系列 Enable 密码 | `qwer1234` |
| 跳板机用户 | `sun` |
| 跳板机密码 | `qwe123` |
| Agent API Key | `cmnet-agent-key-2026` |
| MySQL 用户 | `netops` / `netops123` |

---

## 项目规模

```
Git: master @ v1.0.0 (8 commits)
Backend:  3,960+ lines Python (15 models + 15 routers + 13 services)
Frontend: 2,166+ lines Vue/JS (11 views + 3 components)
Ansible:   119+ lines YAML (5 playbooks + config)
Tests:     43 tests, all passing
Deploy:    Ubuntu 24.04 WSL2
```
