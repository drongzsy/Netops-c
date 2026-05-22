"""seed.py - Initialize CMNET device data from eNSP inventory."""
from app.database import SessionLocal, init_db
from app.models.device import Device, DeviceType, DeviceRole, DeviceStatus
from app.models.credential import Credential, AuthType
from app.models.user import User
from app.services.auth import hash_password
from app.services.crypto import encrypt

# Real credential from eNSP device info table
REAL_PASSWORD_ENC = "gAAAAABqDosLHe4KSypvVJjlUF460eVyCbp4Cj7X-FwCF2YVfVrJcjjuPkmyCgWn3sx51ZBNQ8Ggjgmdfe0OuRdyVDoTxIopEA=="

DEVICES = [
    # S-series management switches (have enable password)
    Device(name="S-1", ip_address="192.168.100.254", device_type=DeviceType.SW, role=DeviceRole.MANAGEMENT, status=DeviceStatus.ONLINE, city="武汉", enable_password="qwer1234"),
    Device(name="S-3", ip_address="192.168.100.253", device_type=DeviceType.SW, role=DeviceRole.MANAGEMENT, status=DeviceStatus.ONLINE, city="武汉", enable_password="qwer1234"),
    Device(name="S-5", ip_address="192.168.100.252", device_type=DeviceType.SW, role=DeviceRole.MANAGEMENT, status=DeviceStatus.ONLINE, city="武汉", enable_password="qwer1234"),
    Device(name="S-11", ip_address="192.168.100.251", device_type=DeviceType.SW, role=DeviceRole.MANAGEMENT, status=DeviceStatus.ONLINE, city="武汉", enable_password="qwer1234"),
    Device(name="S-12", ip_address="192.168.100.250", device_type=DeviceType.SW, role=DeviceRole.MANAGEMENT, status=DeviceStatus.ONLINE, city="武汉", enable_password="qwer1234"),
    # Customer edge (no enable password)
    Device(name="C-1", ip_address="192.168.100.2", device_type=DeviceType.PE, role=DeviceRole.CUSTOMER_EDGE, status=DeviceStatus.ONLINE, city="省外"),
    Device(name="C-2", ip_address="192.168.100.3", device_type=DeviceType.PE, role=DeviceRole.CUSTOMER_EDGE, status=DeviceStatus.ONLINE, city="省外"),
    # BB core
    Device(name="BB-1", ip_address="192.168.100.4", device_type=DeviceType.BB, role=DeviceRole.CORE, status=DeviceStatus.ONLINE, city="省外"),
    Device(name="BB-2", ip_address="192.168.100.5", device_type=DeviceType.BB, role=DeviceRole.CORE, status=DeviceStatus.ONLINE, city="省外"),
    # PB core
    Device(name="PB-1", ip_address="192.168.100.6", device_type=DeviceType.PB, role=DeviceRole.CORE, status=DeviceStatus.ONLINE, city="武汉"),
    Device(name="PB-2", ip_address="192.168.100.7", device_type=DeviceType.PB, role=DeviceRole.CORE, status=DeviceStatus.ONLINE, city="武汉"),
    # VPN route reflectors
    Device(name="VPN_RR-1", ip_address="192.168.100.8", device_type=DeviceType.RR, role=DeviceRole.ROUTE_REFLECTOR, status=DeviceStatus.ONLINE, city="武汉"),
    Device(name="VPN_RR-2", ip_address="192.168.100.9", device_type=DeviceType.RR, role=DeviceRole.ROUTE_REFLECTOR, status=DeviceStatus.ONLINE, city="武汉"),
    # Metro convergence
    Device(name="A_MB_1", ip_address="192.168.100.10", device_type=DeviceType.MB, role=DeviceRole.METRO_CONVERGENCE, status=DeviceStatus.ONLINE, city="武汉"),
    Device(name="A_MB_2", ip_address="192.168.100.11", device_type=DeviceType.MB, role=DeviceRole.METRO_CONVERGENCE, status=DeviceStatus.ONLINE, city="武汉"),
    Device(name="B_MB_1", ip_address="192.168.100.13", device_type=DeviceType.MB, role=DeviceRole.METRO_CONVERGENCE, status=DeviceStatus.ONLINE, city="襄阳"),
    Device(name="B_MB_2", ip_address="192.168.100.14", device_type=DeviceType.MB, role=DeviceRole.METRO_CONVERGENCE, status=DeviceStatus.ONLINE, city="襄阳"),
    # BRAS
    Device(name="A-BRAS", ip_address="192.168.100.12", device_type=DeviceType.BRAS, role=DeviceRole.SERVICE_ACCESS, status=DeviceStatus.ONLINE, city="武汉"),
    Device(name="B-BRAS", ip_address="192.168.100.15", device_type=DeviceType.BRAS, role=DeviceRole.SERVICE_ACCESS, status=DeviceStatus.ONLINE, city="襄阳"),
    # PCs
    Device(name="PC-1", ip_address="192.168.100.16", device_type=DeviceType.PC, role=DeviceRole.ACCESS, status=DeviceStatus.ONLINE, city="武汉"),
    Device(name="PC-2", ip_address="192.168.100.17", device_type=DeviceType.PC, role=DeviceRole.ACCESS, status=DeviceStatus.ONLINE, city="襄阳"),
]


def seed() -> None:
    init_db()
    db = SessionLocal()

    try:
        has_devices = db.query(Device).count() > 0
        has_users = db.query(User).count() > 0

        if has_devices and has_users:
            print("Data already seeded")
            return

        # Create default admin user
        if db.query(User).filter(User.username == "admin").count() == 0:
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            db.add(admin)
            db.flush()
            print("Created admin user (admin / admin123)")

        if not has_devices:
            # Create credential with REAL eNSP password
            cred = Credential(
                name="default",
                username="Rfvbgt#123",
                password_encrypted=REAL_PASSWORD_ENC,
            )
            db.add(cred)
            db.flush()

            for dev in DEVICES:
                dev.credential_id = cred.id
            db.add_all(DEVICES)
            print(f"Seeded {len(DEVICES)} devices and 1 credential")

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
