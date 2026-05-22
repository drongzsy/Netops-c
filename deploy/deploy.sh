#!/bin/bash
set -e

# ============================================================
# NetOps CMNET ??????
# ??? Ubuntu 22.04/24.04 LTS
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[FAIL]${NC} $1"; }

# --- ?? root ---
if [ "$EUID" -ne 0 ]; then
    err "?? root ????: sudo bash deploy.sh"
    exit 1
fi

INSTALL_DIR="/opt/netops"
echo ""
echo "========================================"
echo " NetOps CMNET ????"
echo "========================================"
echo ""

# --- 1. ???? ---
log "?????..."
apt-get update -qq

log "??????..."
apt-get install -y -qq python3 python3-venv python3-pip mysql-server nginx git curl 2>&1 | tail -1

# --- 2. ???? ---
if ! id netops &>/dev/null; then
    useradd -m -s /bin/bash netops
    log "?? netops ??"
fi

# --- 3. ???? ---
mkdir -p $INSTALL_DIR
log "????: $INSTALL_DIR"

# --- 4. ???? ---
cp -r $(dirname "$0")/backend $INSTALL_DIR/
cp -r $(dirname "$0")/frontend $INSTALL_DIR/
cp -r $(dirname "$0")/ansible $INSTALL_DIR/
cp $(dirname "$0")/netops-cmnet.service /etc/systemd/system/netops-cmnet.service
cp $(dirname "$0")/nginx/default.conf /etc/nginx/sites-available/netops-cmnet

# ?? .env
cp $INSTALL_DIR/backend/.env.production $INSTALL_DIR/backend/.env
log "??????"

# --- 5. MySQL ?? ---
log "?? MySQL..."
if ! mysql -u root -e "SELECT 1" &>/dev/null; then
    # ???? MySQL
    mysqld --initialize-insecure --user=mysql 2>/dev/null || true
    systemctl enable mysql
    systemctl start mysql
fi

mysql -u root <<SQL
CREATE DATABASE IF NOT EXISTS netops_cmnet CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'netops'@'localhost' IDENTIFIED BY 'netops123';
GRANT ALL PRIVILEGES ON netops_cmnet.* TO 'netops'@'localhost';
FLUSH PRIVILEGES;
SQL
log "MySQL ??????"

# --- 6. Python ???? ---
log "?? Python ????..."
python3 -m venv $INSTALL_DIR/backend/.venv
source $INSTALL_DIR/backend/.venv/bin/activate
pip install -q --upgrade pip
pip install -q -r $INSTALL_DIR/backend/requirements.txt
log "Python ?????"

# --- 7. ?????? ---
log "??????..."
cd $INSTALL_DIR/backend
source .venv/bin/activate
python seed.py
log "???????"

# --- 8. Nginx ?? ---
log "?? Nginx..."
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/netops-cmnet /etc/nginx/sites-enabled/
systemctl enable nginx
systemctl restart nginx
log "Nginx ???"

# --- 9. ?? ---
chown -R netops:netops $INSTALL_DIR
log "??????"

# --- 10. ???? ---
systemctl daemon-reload
systemctl enable netops-cmnet
systemctl start netops-cmnet
log "NetOps ?????"

# --- 11. ?? ---
sleep 2
if systemctl is-active --quiet netops-cmnet; then
    log "????????"
else
    warn "?????????????: journalctl -u netops-cmnet -n 50"
fi

if curl -s http://localhost/api/health | grep -q "ok"; then
    log "API ??????"
else
    warn "API ??????????????"
fi

echo ""
echo "========================================"
echo -e "${GREEN} ????!${NC}"
echo ""
echo " ????: http://$(hostname -I | awk '{print $1}')"
echo " API??:  http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo " ????: admin / admin123"
echo "========================================"
echo ""
