# Dashboard Access Instructions

## ✅ Dashboard is Running!

The dashboard service is active at:
- **Local**: http://localhost:8501
- **Remote**: http://44.201.26.33:8501

## 🔒 Security Group Configuration Needed

Port 8501 is currently **blocked** by AWS Security Group. To access the dashboard remotely:

### Option 1: Open Port in AWS Console (Recommended)

1. Go to AWS EC2 Console → **Security Groups**
2. Find security group for instance `i-0b403a5684524a722` (dev machine)
3. Click **Edit inbound rules**
4. **Add rule**:
   - Type: Custom TCP
   - Port: 8501
   - Source: **Your IP** (or 0.0.0.0/0 for public access)
   - Description: Weather Dashboard (Streamlit)
5. **Save rules**

Then access: http://44.201.26.33:8501

### Option 2: SSH Tunnel (Temporary Access)

```bash
# On your local machine
ssh -L 8501:localhost:8501 ubuntu@44.201.26.33 -i ~/.ssh/your-key.pem

# Then open in browser:
http://localhost:8501
```

### Option 3: Cloudflare Tunnel (Free HTTPS)

```bash
# On server
cloudflared tunnel --url http://localhost:8501
```

This will give you a temporary `*.trycloudflare.com` URL with HTTPS.

## 🔧 Dashboard Management

```bash
# View logs
sudo journalctl -u weather-dashboard -f

# Restart service
sudo systemctl restart weather-dashboard

# Stop service
sudo systemctl stop weather-dashboard

# Check status
sudo systemctl status weather-dashboard
```

## 📊 Dashboard Features

Once accessible, you'll see:
- **Current Forecast**: Latest ensemble prediction for tomorrow
- **Model Breakdown**: Individual model predictions
- **Performance Charts**: MAE, RMSE, bias for each model
- **Forecast Evolution**: How predictions changed over time
- **Historical Observations**: Recent temperature data

## 🌐 Production Setup (with Domain + HTTPS)

For production deployment with custom domain:

1. Point domain DNS to server IP
2. Run: `./setup_dashboard.sh your-domain.com`
3. Get Let's Encrypt certificate: `sudo certbot --nginx -d your-domain.com`

## 🚨 Troubleshooting

**Dashboard not loading?**
```bash
# Check if service is running
sudo systemctl status weather-dashboard

# Check logs for errors
sudo journalctl -u weather-dashboard -n 50 --no-pager

# Restart service
sudo systemctl restart weather-dashboard
```

**Database errors?**
```bash
# Make sure forecasts have been collected
cd /home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker
./weather_tracker.py forecast
```

**Port 8501 still blocked?**
- Check AWS Security Group rules (must allow TCP 8501)
- Check server firewall: `sudo ufw status` (Ubuntu) or `sudo iptables -L` (general)
