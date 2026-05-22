import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
ANSIBLE_DIR = BASE_DIR.parent / "ansible"
PLAYBOOK_DIR = ANSIBLE_DIR / "playbooks"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://netops:netops123@localhost:3306/netops_cmnet?charset=utf8mb4",
)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", None)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

# Ansible execution mode: "wsl" (Windows→WSL), "ssh" (remote host), "local" (direct)
ANSIBLE_MODE = os.getenv("ANSIBLE_MODE", "wsl")
ANSIBLE_REMOTE_HOST = os.getenv("ANSIBLE_REMOTE_HOST", "")
ANSIBLE_REMOTE_USER = os.getenv("ANSIBLE_REMOTE_USER", "")
ANSIBLE_REMOTE_KEY = os.getenv("ANSIBLE_REMOTE_KEY", "")
# WSL: path where Windows project root is mounted (e.g. /mnt/c/Users/CMCC/netops-cmnet)
ANSIBLE_WSL_PROJECT_PATH = os.getenv("ANSIBLE_WSL_PROJECT_PATH", "")

# Agent API
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")  # set to enable API-Key auth for agents

# SSH jump host / bastion for reaching eNSP devices
ANSIBLE_JUMP_HOST = os.getenv("ANSIBLE_JUMP_HOST", "")  # set IP to enable jump host
ANSIBLE_JUMP_USER = os.getenv("ANSIBLE_JUMP_USER", "sun")
ANSIBLE_JUMP_PASS = os.getenv("ANSIBLE_JUMP_PASS", "Qwe123")
