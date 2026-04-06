#!/bin/bash
#
# Quick Dashboard Setup (HTTP only, no domain)
# For production HTTPS, use setup_dashboard.sh with domain
#

set -e

PROJECT_DIR="/home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker"

echo "🚀 Setting up Weather Forecast Dashboard..."

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/weather-dashboard.service > /dev/null <<EOF
[Unit]
Description=Weather Forecast Dashboard (Streamlit)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$PROJECT_DIR
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m streamlit run dashboard.py --server.port=8501 --server.address=127.0.0.1 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start service
echo "Starting dashboard service..."
sudo systemctl daemon-reload
sudo systemctl enable weather-dashboard
sudo systemctl restart weather-dashboard
sleep 2

# Check status
if sudo systemctl is-active --quiet weather-dashboard; then
    echo "✅ Dashboard service running"
else
    echo "❌ Dashboard service failed to start"
    sudo journalctl -u weather-dashboard -n 20 --no-pager
    exit 1
fi

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo ""
echo "✅ Dashboard running!"
echo ""
echo "Access via:"
echo "  Local:  http://localhost:8501"
echo "  Remote: http://$PUBLIC_IP:8501"
echo ""
echo "⚠️  Port 8501 must be open in security group!"
echo ""
echo "Commands:"
echo "  Stop:    sudo systemctl stop weather-dashboard"
echo "  Restart: sudo systemctl restart weather-dashboard"
echo "  Logs:    sudo journalctl -u weather-dashboard -f"
echo "  Status:  sudo systemctl status weather-dashboard"
