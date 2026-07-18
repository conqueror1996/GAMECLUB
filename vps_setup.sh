#!/bin/bash
# =====================================================
# Paste this INSIDE the VPS SSH session
# After: ssh root@152.228.227.85 -p 20008
# =====================================================

set -e

echo "==> [1/6] Updating system..."
apt-get update -qq && apt-get upgrade -y -qq

echo "==> [2/6] Installing dependencies..."
apt-get install -y python3 python3-pip python3-venv git curl

echo "==> [3/6] Cloning repo..."
if [ -d "/opt/dualhedge" ]; then
    cd /opt/dualhedge && git pull origin main
else
    git clone https://github.com/conqueror1996/DUALHEDGE.git /opt/dualhedge
fi

cd /opt/dualhedge

echo "==> [4/6] Installing Python packages..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements.txt -q

echo "==> [5/6] Creating systemd service..."
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
systemctl start dualhedge

echo "==> [6/6] Opening firewall port 5000..."
ufw allow 5000/tcp 2>/dev/null || iptables -A INPUT -p tcp --dport 5000 -j ACCEPT 2>/dev/null || true

sleep 3
echo ""
echo "==> Service status:"
systemctl status dualhedge --no-pager | head -15

echo ""
echo "======================================"
echo "  ✅ DONE!"
echo "  Dashboard: http://152.228.227.85:5000"
echo "  Logs:  journalctl -u dualhedge -f"
echo "======================================"
