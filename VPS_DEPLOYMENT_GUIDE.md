# VPS Deployment Guide for 1vCPU / 1GB RAM Server

## System Requirements
- **VPS**: 1vCPU, 1GB RAM minimum
- **OS**: Ubuntu 20.04/22.04 LTS (recommended)
- **Disk**: 10GB+ (for OS, dependencies, and saved images)
- **Network**: Open port 5001 (or your preferred port)

---

## Deployment Steps

### 1. Update System & Install Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx -y
```

### 2. Create Application Directory
```bash
mkdir -p ~/iot-backend
cd ~/iot-backend
```

### 3. Upload Your Files
Upload these files to the VPS:
- `backend_server.py`
- `requirements_production.txt`
- `model/model.tflite`
- `model/labels.txt`

```bash
# Using SCP from your local machine:
scp -r iot/* user@your-vps-ip:~/iot-backend/
```

### 4. Create Virtual Environment
```bash
cd ~/iot-backend
python3 -m venv venv
source venv/bin/activate
```

### 5. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements_production.txt
```

### 6. Test the Application
```bash
python backend_server.py
```
Access: `http://your-vps-ip:5001/health`

---

## Production Deployment with Gunicorn

### Create Systemd Service
Create file: `/etc/systemd/system/iot-backend.service`

```bash
sudo nano /etc/systemd/system/iot-backend.service
```

Paste this configuration:
```ini
[Unit]
Description=IoT Material Identification Backend
After=network.target

[Service]
Type=notify
User=your-username
Group=www-data
WorkingDirectory=/home/your-username/iot-backend
Environment="PATH=/home/your-username/iot-backend/venv/bin"
ExecStart=/home/your-username/iot-backend/venv/bin/gunicorn \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --bind 0.0.0.0:5001 \
    --access-logfile /var/log/iot-backend/access.log \
    --error-logfile /var/log/iot-backend/error.log \
    backend_server:app

# Resource limits for 1GB RAM VPS
MemoryMax=800M
MemoryHigh=600M

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Replace `your-username` with your actual username.

### Create Log Directory
```bash
sudo mkdir -p /var/log/iot-backend
sudo chown your-username:www-data /var/log/iot-backend
```

### Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable iot-backend
sudo systemctl start iot-backend
sudo systemctl status iot-backend
```

---

## Optional: Nginx Reverse Proxy (Recommended)

### Configure Nginx
Create file: `/etc/nginx/sites-available/iot-backend`

```bash
sudo nano /etc/nginx/sites-available/iot-backend
```

Paste this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # or your VPS IP

    # Increase max upload size for images
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/iot-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Resource Optimization Tips

### 1. Limit Image Saving (Save Disk Space)
Edit `backend_server.py`:
```python
SAVE_IMAGES = False  # Disable if running low on disk space
```

Or implement auto-cleanup:
```bash
# Crontab to delete old images (keep only last 7 days)
crontab -e

# Add this line:
0 2 * * * find ~/iot-backend/saved_images -type f -mtime +7 -delete
```

### 2. Monitor Memory Usage
```bash
# Install monitoring
sudo apt install htop

# Check memory
htop

# Check specific process
ps aux | grep gunicorn
```

### 3. Enable Swap (if needed)
```bash
# Create 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Firewall Configuration

```bash
# Allow SSH (if not already allowed)
sudo ufw allow 22/tcp

# Allow HTTP (if using Nginx)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow direct API access (if not using Nginx)
sudo ufw allow 5001/tcp

# Enable firewall
sudo ufw enable
```

---

## Monitoring & Maintenance

### Check Service Status
```bash
sudo systemctl status iot-backend
```

### View Logs
```bash
# Application logs
sudo tail -f /var/log/iot-backend/access.log
sudo tail -f /var/log/iot-backend/error.log

# System logs
sudo journalctl -u iot-backend -f
```

### Restart Service
```bash
sudo systemctl restart iot-backend
```

### Update Application
```bash
cd ~/iot-backend
source venv/bin/activate
git pull  # or upload new files
pip install -r requirements_production.txt --upgrade
sudo systemctl restart iot-backend
```

---

## Performance Expectations on 1vCPU/1GB RAM

- **Concurrent Requests**: 2-5 simultaneous requests
- **Response Time**: 0.5-2 seconds per image
- **Memory Usage**: 200-400 MB
- **Uptime**: 99%+ with proper configuration

---

## Troubleshooting

### Out of Memory?
```bash
# Check memory usage
free -h

# Reduce workers in gunicorn
# Edit /etc/systemd/system/iot-backend.service
--workers 1  # Instead of 2
```

### Slow Response?
```bash
# Check CPU usage
top

# Consider upgrading to 2vCPU VPS
# or reduce concurrent requests
```

### Port Already in Use?
```bash
# Check what's using port 5001
sudo lsof -i :5001

# Kill process if needed
sudo kill -9 <PID>
```

---

## Cost Estimate

**VPS Providers** (1vCPU, 1GB RAM):
- **DigitalOcean**: $6/month (Droplet)
- **Linode**: $5/month (Nanode)
- **Vultr**: $5/month
- **AWS Lightsail**: $3.50/month
- **Google Cloud**: ~$5/month (e2-micro)

**Recommended**: Start with a $5-6/month VPS, monitor usage, and upgrade if needed.

---

## SSL/HTTPS (Optional but Recommended)

Using Let's Encrypt (Free):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo systemctl restart nginx
```

---

## Backup Strategy

```bash
# Backup model and saved images
tar -czf backup-$(date +%Y%m%d).tar.gz model/ saved_images/

# Upload to cloud storage or download
scp user@vps-ip:~/iot-backend/backup-*.tar.gz ./
```

---

## Summary

✅ **YES**: This app can run on 1vCPU/1GB RAM VPS
✅ **Recommended**: Use gunicorn + nginx for production
✅ **Cost**: ~$5/month
✅ **Performance**: Handles 2-5 concurrent requests efficiently
✅ **Scalability**: Can upgrade to 2vCPU/2GB RAM if traffic increases

Your application is lightweight enough for a minimal VPS! 🚀
