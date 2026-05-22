"""Tests for SQLAlchemy models — Device and Credential."""

from app.models.credential import AuthType, Credential
from app.models.device import Device, DeviceRole, DeviceStatus, DeviceType
from app.services.crypto import encrypt


def test_create_device(db_session):
    dev = Device(
        name="test-device",
        ip_address="10.0.0.1",
        device_type=DeviceType.CR,
        role=DeviceRole.CORE,
    )
    db_session.add(dev)
    db_session.commit()
    assert dev.id is not None
    assert dev.status == DeviceStatus.UNKNOWN


def test_device_default_status(db_session):
    dev = Device(
        name="test-device-2",
        ip_address="10.0.0.2",
        device_type=DeviceType.PB,
        role=DeviceRole.CORE,
    )
    db_session.add(dev)
    db_session.commit()
    assert dev.status == DeviceStatus.UNKNOWN


def test_device_unique_name(db_session):
    dev1 = Device(name="unique", ip_address="10.0.0.1", device_type=DeviceType.SW, role=DeviceRole.MANAGEMENT)
    db_session.add(dev1)
    db_session.commit()
    dev2 = Device(name="unique", ip_address="10.0.0.2", device_type=DeviceType.SW, role=DeviceRole.MANAGEMENT)
    db_session.add(dev2)
    import pytest
    with pytest.raises(Exception):
        db_session.commit()


def test_create_credential(db_session):
    cred = Credential(
        name="test-creds",
        username="admin",
        password_encrypted=encrypt("secret123"),
    )
    db_session.add(cred)
    db_session.commit()
    assert cred.id is not None
    assert cred.auth_type == AuthType.PASSWORD


def test_credential_name_unique(db_session):
    c1 = Credential(name="dup-name", username="user1", password_encrypted=encrypt("a"))
    db_session.add(c1)
    db_session.commit()
    c2 = Credential(name="dup-name", username="user2", password_encrypted=encrypt("b"))
    db_session.add(c2)
    import pytest
    with pytest.raises(Exception):
        db_session.commit()


def test_device_credential_relationship(db_session):
    cred = Credential(name="rel-creds", username="netops", password_encrypted=encrypt("pass"))
    db_session.add(cred)
    db_session.flush()
    dev = Device(
        name="rel-device",
        ip_address="10.0.0.1",
        device_type=DeviceType.PE,
        role=DeviceRole.CUSTOMER_EDGE,
        credential_id=cred.id,
    )
    db_session.add(dev)
    db_session.commit()
    assert dev.credential_id == cred.id
    assert dev.credential.username == "netops"
