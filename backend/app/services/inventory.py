from sqlalchemy.orm import Session

from ..config import ANSIBLE_JUMP_HOST, ANSIBLE_JUMP_PASS, ANSIBLE_JUMP_USER
from ..models.credential import Credential
from ..models.device import Device
from .crypto import decrypt


def _proxy_args() -> str:
    """Return ssh_common_args if jump host is configured, else empty string."""
    if not ANSIBLE_JUMP_HOST:
        return ""
    proxy = (
        f"sshpass -p '{ANSIBLE_JUMP_PASS}' "
        f"ssh -W %h:%p -o StrictHostKeyChecking=no "
        f"{ANSIBLE_JUMP_USER}@{ANSIBLE_JUMP_HOST}"
    )
    return f"-o ProxyCommand=\"{proxy}\""


def build_inventory(device_ids: list[int], db: Session) -> dict:
    """Build Ansible inventory with real credential values for Huawei CE devices."""
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
    groups: dict[str, dict] = {}
    name_to_id: dict[str, int] = {}

    proxy_args = _proxy_args()

    for dev in devices:
        dev_group = dev.device_type.value
        if dev_group not in groups:
            groups[dev_group] = {"hosts": {}}

        username = "admin"
        password = ""
        if dev.credential_id:
            cred = db.query(Credential).filter(Credential.id == dev.credential_id).first()
            if cred:
                username = cred.username
                password = decrypt(cred.password_encrypted)

        # Note: StrictHostKeyChecking=no is needed for first contact with eNSP devices
        host_vars = {
            "ansible_host": dev.ip_address,
            "ansible_user": username,
            "ansible_ssh_pass": password,
            "ansible_connection": "ansible.netcommon.network_cli",
            "ansible_network_os": "community.network.ce",
            "ansible_ssh_common_args": "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",
        }
        if dev.enable_password:
            host_vars["ansible_become"] = "yes"
            host_vars["ansible_become_method"] = "enable"
            host_vars["ansible_become_pass"] = dev.enable_password
        if proxy_args:
            host_vars["ansible_ssh_common_args"] = proxy_args
        groups[dev_group]["hosts"][dev.name] = host_vars
        name_to_id[dev.name] = dev.id

    return {
        "all": {"children": groups},
        "_meta": {"name_to_id": name_to_id},
    }
