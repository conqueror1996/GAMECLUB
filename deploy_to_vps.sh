#!/bin/bash
# ============================================================
# DualHedge VPS Deploy Script
# Target: 152.228.227.85:20008 (Ubuntu 24.04)
# Run: bash deploy_to_vps.sh
# ============================================================

VPS_IP="152.228.227.85"
VPS_PORT="20008"
VPS_USER="root"
REPO="https://github.com/conqueror1996/dualheding.git"

echo "=================================================="
echo "  DualHedge VPS Deployment"
echo "  Target: $VPS_USER@$VPS_IP:$VPS_PORT"
echo "=================================================="

ssh -p $VPS_PORT $VPS_USER@$VPS_IP -o StrictHostKeyChecking=no << 'ENDSSH'

echo "==> Updating system..."
apt-get update -qq && apt-get upgrade -y -qq

echo "==> Installing Python3, pip, git, screen..."
apt-get install -y -qq python3 python3-pip python3-venv git curl

echo "==> Cloning/updating repo..."
if [ -d "/opt/dualhedge" ]; then
    cd /opt/dualhedge && git pull origin main
else
    git clone https://github.com/conqueror1996/DUALHEDGE.git /opt/dualhedge
fi

cd /opt/dualhedge

echo "==> Setting up Python venv..."
python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

echo "==> Creating systemd service..."
cat > /etc/systemd/system/dualhedge.service << 'EOF'
[Unit]
Description=DualHedge Auto-Bet System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/dualhedge
ExecStart=/opt/dualhedge/venv/bin/python3 app.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dualhedge
systemctl restart dualhedge

echo "==> Allowing port 5000..."
ufw allow 5000/tcp 2>/dev/null || true

sleep 5
systemctl status dualhedge --no-pager | head -20

echo ""
echo "Dashboard: http://152.228.227.85:5000"
echo "Logs: journalctl -u dualhedge -f"

ENDSSH
