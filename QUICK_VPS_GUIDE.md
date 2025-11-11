# Quick VPS Deployment Guide

## Step 1: Upload Files to VPS

From your local machine:

```bash
# Replace user@your-vps-ip with your actual VPS credentials
scp backend_api.py user@your-vps-ip:~/
scp -r model user@your-vps-ip:~/
scp vps_setup.sh user@your-vps-ip:~/
```

## Step 2: Connect to VPS

```bash
ssh user@your-vps-ip
```

## Step 3: Run Setup Script

```bash
chmod +x vps_setup.sh
./vps_setup.sh
```

## Step 4: Run the API

### Option A: Quick Test (Development)
```bash
source venv/bin/activate
python backend_api.py
```
Press `Ctrl+C` to stop.

### Option B: Production with Gunicorn (Recommended)
```bash
source venv/bin/activate
gunicorn -w 2 -b 0.0.0.0:5001 --timeout 120 backend_api:app
```

### Option C: Run in Background
```bash
source venv/bin/activate
nohup gunicorn -w 2 -b 0.0.0.0:5001 --timeout 120 backend_api:app > api.log 2>&1 &
```

Check if running:
```bash
ps aux | grep gunicorn
```

View logs:
```bash
tail -f api.log
```

Stop background process:
```bash
pkill -f gunicorn
```

## Step 5: Configure Firewall

```bash
# Allow port 5001
sudo ufw allow 5001/tcp
sudo ufw enable
```

## Step 6: Test API

From your local machine:
```bash
# Test health endpoint
curl http://your-vps-ip:5001/health

# Test material detection (with an image)
curl -X POST http://your-vps-ip:5001/identify/material \
  -H "Content-Type: image/jpeg" \
  --data-binary "@test_image.jpg"
```

## Optional: Run as System Service

Create service file:
```bash
sudo nano /etc/systemd/system/material-api.service
```

Paste this (replace `your-username`):
```ini
[Unit]
Description=Material Identification API
After=network.target

[Service]
Type=notify
User=your-username
WorkingDirectory=/home/your-username
Environment="PATH=/home/your-username/venv/bin"
ExecStart=/home/your-username/venv/bin/gunicorn -w 2 -b 0.0.0.0:5001 --timeout 120 backend_api:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable material-api
sudo systemctl start material-api
sudo systemctl status material-api
```

## Useful Commands

```bash
# View logs
sudo journalctl -u material-api -f

# Restart service
sudo systemctl restart material-api

# Stop service
sudo systemctl stop material-api

# Check status
sudo systemctl status material-api
```

## Troubleshooting

### Port already in use?
```bash
sudo lsof -i :5001
sudo kill -9 <PID>
```

### Check if service is running?
```bash
curl http://localhost:5001/health
```

### View Python errors?
```bash
tail -f api.log
```

---

**That's it! Your API should now be running on your VPS.** 🚀

Access it at: `http://your-vps-ip:5001`
