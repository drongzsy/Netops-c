import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

from ..config import (
    ANSIBLE_MODE,
    ANSIBLE_REMOTE_HOST,
    ANSIBLE_REMOTE_KEY,
    ANSIBLE_REMOTE_USER,
    ANSIBLE_WSL_PROJECT_PATH,
    PLAYBOOK_DIR,
)

try:
    import ansible_runner  # noqa: F401

    HAS_RUNNER = True
except ImportError:
    HAS_RUNNER = False


def run_playbook(
    playbook: str,
    inventory: dict,
    extra_vars: dict | None = None,
) -> dict:
    """Run an Ansible playbook.

    Execution mode is controlled by ANSIBLE_MODE config:
      - "wsl":  invoke WSL's ansible-playbook from Windows
      - "ssh":  SSH to a remote Ansible controller
      - "local": run ansible-playbook directly (Linux/WSL)

    Args:
        playbook: Filename in PLAYBOOK_DIR (e.g. "backup.yml").
        inventory: Ansible inventory dict (from build_inventory).
        extra_vars: Extra variables passed via --extra-vars.

    Returns:
        dict with keys: status, rc, stdout, stderr, parsed.
    """
    playbook_path = PLAYBOOK_DIR / playbook
    if not playbook_path.exists():
        raise FileNotFoundError(f"Playbook not found: {playbook_path}")

    inv_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(inventory, inv_file, ensure_ascii=False)
    inv_file.close()

    try:
        if ANSIBLE_MODE == "wsl":
            return _run_via_wsl(playbook_path, inv_file.name, extra_vars)
        elif ANSIBLE_MODE == "ssh":
            return _run_via_ssh(playbook_path, inv_file.name, extra_vars)
        elif platform.system() == "Windows" and HAS_RUNNER:
            return _run_via_runner(playbook_path, inv_file.name, extra_vars)
        else:
            return _run_via_subprocess(playbook_path, inv_file.name, extra_vars)
    finally:
        _cleanup(inv_file.name)


# ── WSL execution ──────────────────────────────────────────────────────────


def _to_wsl_path(win_path: str) -> str:
    r"""Convert a Windows path to a WSL /mnt/ path.

    C:\Users\CMCC\netops-cmnet -> /mnt/c/Users/CMCC/netops-cmnet
    """
    if ANSIBLE_WSL_PROJECT_PATH:
        # User explicitly configured the WSL mount point
        rel = Path(win_path).relative_to(PLAYBOOK_DIR.parent.parent)
        return f"{ANSIBLE_WSL_PROJECT_PATH.rstrip('/')}/{rel.as_posix()}"
    # Auto-convert using drive letter
    drive = Path(win_path).drive[0].lower()
    rest = Path(win_path).as_posix()[2:]  # strip "C:" → keep "/..."
    return f"/mnt/{drive}{rest}"


def _run_via_wsl(
    playbook_path: Path, inv_file: str, extra_vars: dict | None
) -> dict:
    """Run ansible-playbook via WSL (using venv with paramiko)."""
    wsl_playbook = _to_wsl_path(str(playbook_path))
    wsl_inventory = _to_wsl_path(inv_file)
    # Build extra_vars CLI args
    extra_args = ""
    for k, v in (extra_vars or {}).items():
        if isinstance(v, list):
            extra_args += f" -e '{k}={json.dumps(v)}'"
        else:
            extra_args += f" -e '{k}={v}'"

    # Write a temp wrapper script (avoids bash -c argument issues)
    script_path = playbook_path.parent / ".run_ansible.sh"
    ansible_cfg_path = _to_wsl_path(str(PLAYBOOK_DIR.parent / "ansible.cfg"))
    script = (
        '#!/bin/bash\n'
        f'export ANSIBLE_CONFIG="{ansible_cfg_path}"\n'
        f'ansible-playbook "{wsl_playbook}" -i "{wsl_inventory}"{extra_args}\n'
    )
    # Write with LF line endings (avoid CRLF breaking bash on WSL)
    script_path.write_bytes(script.encode("utf-8"))
    os.chmod(str(script_path), 0o755)

    wsl_script = _to_wsl_path(str(script_path))

    try:
        result = subprocess.run(
            ["wsl", "bash", wsl_script],
            capture_output=True, text=True, timeout=300,
        )
    except subprocess.TimeoutExpired:
        return {"status": "failed", "rc": -1, "stdout": "", "stderr": "Timeout (300s)", "parsed": None}
    finally:
        script_path.unlink(missing_ok=True)

    parsed = _parse_json_output(result.stdout)
    return {
        "status": "success" if result.returncode == 0 else "failed",
        "rc": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "parsed": parsed,
    }


# ── SSH execution ──────────────────────────────────────────────────────────


def _run_via_ssh(
    playbook_path: Path, inv_file: str, extra_vars: dict | None
) -> dict:
    """SCP playbook + inventory to remote host, run ansible-playbook via SSH."""
    remote_dir = "/tmp/netops_ansible"
    playbook_name = playbook_path.name

    ssh_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    if ANSIBLE_REMOTE_KEY:
        ssh_opts += f" -i {ANSIBLE_REMOTE_KEY}"
    dest = f"{ANSIBLE_REMOTE_USER}@{ANSIBLE_REMOTE_HOST}"

    try:
        _ssh(f"mkdir -p {remote_dir}", ssh_opts, dest)
        _scp(str(playbook_path), f"{dest}:{remote_dir}/{playbook_name}", ssh_opts)
        _scp(inv_file, f"{dest}:{remote_dir}/inventory.json", ssh_opts)

        extra_args = ""
        for k, v in (extra_vars or {}).items():
            if isinstance(v, list):
                extra_args += f" -e '{k}={json.dumps(v)}'"
            else:
                extra_args += f" -e '{k}={v}'"

        rc, stdout, stderr = _ssh(
            f"cd {remote_dir} && ansible-playbook {playbook_name} -i inventory.json{extra_args}",
            ssh_opts,
            dest,
        )

        parsed = _parse_json_output(stdout)
        return {
            "status": "success" if rc == 0 else "failed",
            "rc": rc,
            "stdout": stdout,
            "stderr": stderr,
            "parsed": parsed,
        }
    except Exception as e:
        return {"status": "failed", "rc": -1, "stdout": "", "stderr": str(e), "parsed": None}


def _ssh(cmd: str, opts: str, dest: str) -> tuple[int, str, str]:
    full = f"ssh {opts} {dest} {cmd}"
    r = subprocess.run(full, shell=True, capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout, r.stderr


def _scp(src: str, dst: str, opts: str) -> None:
    subprocess.run(
        f"scp {opts} {src} {dst}",
        shell=True,
        capture_output=True,
        text=True,
        timeout=120,
    )


# ── Local execution (existing) ─────────────────────────────────────────────


def _run_via_runner(
    playbook_path: Path, inv_file: str, extra_vars: dict | None
) -> dict:
    import ansible_runner

    r = ansible_runner.run(
        playbook=str(playbook_path),
        inventory=inv_file,
        extravars=extra_vars or {},
        json_mode=True,
    )
    return {
        "status": "success" if r.status == "successful" else "failed",
        "rc": r.rc,
        "stdout": "",
        "stderr": "",
        "parsed": _collect_runner_events(r),
    }


def _collect_runner_events(runner_result) -> list[dict]:
    events = []
    for e in runner_result.events:
        event = e.get("event", "")
        if event in ("runner_on_ok", "runner_on_failed"):
            events.append(e)
    return events


def _run_via_subprocess(
    playbook_path: Path, inv_file: str, extra_vars: dict | None
) -> dict:
    cmd = [
        "ansible-playbook",
        str(playbook_path),
        "-i",
        inv_file,
    ]
    for k, v in (extra_vars or {}).items():
        if isinstance(v, list):
            cmd.extend(["-e", f"{k}={json.dumps(v)}"])
        else:
            cmd.extend(["-e", f"{k}={v}"])

    result = subprocess.run(cmd, capture_output=True, text=True)
    parsed = _parse_json_output(result.stdout)

    return {
        "status": "success" if result.returncode == 0 else "failed",
        "rc": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "parsed": parsed,
    }


# ── Shared helpers ─────────────────────────────────────────────────────────


def _parse_json_output(stdout: str) -> dict | None:
    """Extract the JSON object from ansible-playbook stdout (json callback)."""
    # The json callback outputs a single multi-line JSON object
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        pass
    # Fallback: try line-by-line for other formats
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def _cleanup(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass
