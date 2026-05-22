"""Tests for Huawei CE CLI output parsers."""

from app.services.result_parser import (
    check_acl_compliance,
    check_bgp_compliance,
    check_ntp_compliance,
    check_snmp_compliance,
    parse_cpu,
    parse_interfaces,
    parse_memory,
)


def test_parse_cpu_success():
    text = "CPU Usage Stats : 45%   last 5 minutes"
    assert parse_cpu(text) == 45.0


def test_parse_cpu_no_match():
    assert parse_cpu("no cpu data here") is None


def test_parse_cpu_empty():
    assert parse_cpu("") is None


def test_parse_memory_success():
    text = "Memory Util. Stat. : 62%  total 8192 MB"
    assert parse_memory(text) == 62.0


def test_parse_memory_no_match():
    assert parse_memory("no memory info") is None


def test_parse_interfaces_counts():
    text = (
        "Interface                   IP/Mask              Status    Protocol\n"
        "GE0/0/1                     10.0.0.1/24          up        up\n"
        "GE0/0/2                     10.0.0.2/24          down      down\n"
        "GE0/0/3                     10.0.0.3/24          up        up\n"
    )
    result = parse_interfaces(text)
    assert any(r["type"] == "interface_up" and r["value"] == 2 for r in result)
    assert any(r["type"] == "interface_down" and r["value"] == 1 for r in result)


def test_parse_interfaces_all_down():
    text = "Interface IP/Mask Status Protocol\nGE0/0/1 10.0.0.1/24 down down\nGE0/0/2 10.0.0.2/24 down down\n"
    result = parse_interfaces(text)
    assert any(r["type"] == "interface_up" and r["value"] == 0 for r in result)
    assert any(r["type"] == "interface_down" and r["value"] == 2 for r in result)


def test_parse_interfaces_four_columns_required():
    text = "GE0/0/1 up\nGE0/0/2 down\n"
    result = parse_interfaces(text)
    # Lines with < 4 columns are skipped
    assert result == []


def test_parse_interfaces_empty():
    assert parse_interfaces("") == []


def test_snmp_compliance_default_community():
    text = "snmp-agent community read public"
    result = check_snmp_compliance(text)
    assert any(r["status"] == "fail" for r in result)
    assert any("public" in r["detail"] for r in result)


def test_snmp_compliance_custom_community():
    text = "snmp-agent community read mycustomcommunity"
    result = check_snmp_compliance(text)
    assert any(r["status"] == "pass" for r in result)


def test_snmp_compliance_no_community():
    result = check_snmp_compliance("no snmp config here")
    assert any(r["status"] == "fail" for r in result)


def test_bgp_compliance_established():
    text = "BGP peer 10.0.0.1:  Established\nBGP peer 10.0.0.2:  Established"
    result = check_bgp_compliance(text)
    assert any(r["status"] == "pass" for r in result)


def test_bgp_compliance_no_peers():
    text = "BGP peer 10.0.0.1:  Idle"
    result = check_bgp_compliance(text)
    assert any(r["status"] == "fail" for r in result)


def test_ntp_compliance_configured():
    text = "ntp-service server 10.0.0.1"
    result = check_ntp_compliance(text)
    assert any(r["status"] == "pass" for r in result)


def test_ntp_compliance_missing():
    result = check_ntp_compliance("snmp-agent community read public")
    assert any(r["status"] == "fail" for r in result)


def test_acl_compliance_configured():
    text = "acl number 3001\nacl number 3002"
    result = check_acl_compliance(text)
    assert any(r["status"] == "pass" for r in result)
