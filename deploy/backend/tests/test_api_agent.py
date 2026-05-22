"""Integration tests for Agent API and tool layer."""


def test_agent_health_no_auth(client):
    """Health endpoint should be accessible without auth."""
    resp = client.get("/api/agent/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["service"] == "NetOps Agent API"


def test_agent_devices_requires_auth(client):
    """Protected agent endpoint should reject unauthenticated requests."""
    resp = client.get("/api/agent/devices")
    assert resp.status_code == 401


def test_tool_definitions_with_api_key(client):
    """Tool definitions should be accessible with API-Key."""
    resp = client.get("/api/agent/tools/definitions", headers={"X-API-Key": "cmnet-agent-key-2026"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    tools = data["data"]["tools"]
    assert len(tools) >= 10
    tool_names = [t["function"]["name"] for t in tools]
    assert "network_status" in tool_names
    assert "diagnose_device" in tool_names
    assert "backup_all_devices" in tool_names
    assert "compliance_check" in tool_names


def test_tool_definitions_with_jwt(client, admin_user):
    """Tool definitions should also be accessible with JWT token."""
    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login.json()["access_token"]
    resp = client.get("/api/agent/tools/definitions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["data"]["tools"]) >= 10


def test_tool_definitions_requires_auth(client):
    """Tool definitions should reject unauthenticated requests."""
    resp = client.get("/api/agent/tools/definitions")
    assert resp.status_code == 401


def test_network_status_with_auth(client, auth_header):
    """Network status should return device data with valid auth."""
    resp = client.get("/api/agent/network/status", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    # Should have device counts even if zero
    assert "total_devices" in data["data"]
    assert "online_rate" in data["data"]


def test_agent_chat_with_auth(client, auth_header):
    """Chat endpoint should accept messages and return tool info."""
    resp = client.post(
        "/api/agent/chat",
        headers=auth_header,
        json={"message": "检查全网设备状态"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["available_tools"] >= 10


def test_device_list_with_auth(client, auth_header, db_session):
    """Device list should return proper meta."""
    from app.models.device import Device, DeviceType, DeviceRole
    db_session.add(Device(name="PB-1", ip_address="10.0.0.1", device_type=DeviceType.PB, role=DeviceRole.CORE))
    db_session.commit()

    resp = client.get("/api/agent/devices", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["meta"]["total"] >= 1


def test_diagnose_nonexistent_device(client, auth_header):
    """Diagnose should return error for invalid device ID."""
    resp = client.get("/api/agent/devices/99999/diagnose", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error"] is not None
