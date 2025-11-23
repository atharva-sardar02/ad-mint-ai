# Deployment Quick Reference

Quick command reference for deploying and managing Ad Mint AI in production.

## 🚀 Initial Deployment (One-Time Setup)

### 1. Create S3 Buckets
```bash
# Frontend bucket
aws s3 mb s3://ad-mint-ai-frontend --region us-east-1
aws s3 website s3://ad-mint-ai-frontend/ --index-document index.html --error-document index.html

# Videos bucket
aws s3 mb s3://ad-mint-ai-videos --region us-east-1
aws s3api put-bucket-versioning --bucket ad-mint-ai-videos --versioning-configuration Status=Enabled
```

### 2. Launch EC2 Instance
```bash
# Get VPC and create security group (see DEPLOYMENT_STEPS.md for full commands)
# Launch instance with Ubuntu 22.04, t3.medium
# Save EC2 IP address
```

### 3. Deploy Backend
```bash
# SSH to EC2
ssh -i ad-mint-ai-key.pem ubuntu@YOUR_EC2_IP

# Clone and deploy
cd /var/www/ad-mint-ai
git clone https://github.com/YOUR_USERNAME/ad-mint-ai.git .
chmod +x deployment/deploy.sh
sudo ./deployment/deploy.sh /var/www/ad-mint-ai

# Configure .env
sudo nano /var/www/ad-mint-ai/backend/.env
# (Add all environment variables)

# Restart services
sudo systemctl restart fastapi
sudo systemctl restart nginx
```

### 4. Deploy Frontend
```bash
# From local machine
cd frontend
export VITE_API_URL=http://YOUR_EC2_IP
npm run build
aws s3 sync dist/ s3://ad-mint-ai-frontend/ --delete
```

---

## 🔄 Regular Updates

### Update Backend
```bash
ssh -i ad-mint-ai-key.pem ubuntu@YOUR_EC2_IP
cd /var/www/ad-mint-ai
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
python -m app.db.init_db  # If schema changed
deactivate
sudo systemctl restart fastapi
```

### Update Frontend
```bash
cd frontend
export VITE_API_URL=http://YOUR_EC2_IP
npm run build
aws s3 sync dist/ s3://ad-mint-ai-frontend/ --delete
```

---

## 🔍 Monitoring & Debugging

### Check Service Status
```bash
sudo systemctl status fastapi
sudo systemctl status nginx
```

### View Logs
```bash
# FastAPI logs
sudo journalctl -u fastapi -f

# Nginx error logs
sudo tail -f /var/log/nginx/ad-mint-ai-error.log

# Nginx access logs
sudo tail -f /var/log/nginx/ad-mint-ai-access.log
```

### Test Health Endpoint
```bash
# From EC2
curl http://127.0.0.1:8000/api/health

# From local machine
curl http://YOUR_EC2_IP/api/health
```

---

## 🛠️ Service Management

### FastAPI Service
```bash
sudo systemctl start fastapi      # Start
sudo systemctl stop fastapi       # Stop
sudo systemctl restart fastapi    # Restart
sudo systemctl status fastapi     # Status
sudo journalctl -u fastapi -f     # Logs
```

### Nginx Service
```bash
sudo systemctl reload nginx       # Reload (no downtime)
sudo systemctl restart nginx      # Restart
sudo nginx -t                     # Test config
sudo tail -f /var/log/nginx/ad-mint-ai-error.log  # Error logs
```

---

## 🗄️ Database Management

### Initialize Database
```bash
cd /var/www/ad-mint-ai/backend
source venv/bin/activate
python -m app.db.init_db
deactivate
```

### Test PostgreSQL Connection (if using RDS)
```bash
psql -h RDS_ENDPOINT -U ad_mint_user -d ad_mint_ai
```

---

## 🔐 Environment Variables

### Generate Secret Key
```bash
openssl rand -hex 32
```

### Edit .env File
```bash
sudo nano /var/www/ad-mint-ai/backend/.env
```

### Set Permissions
```bash
sudo chmod 600 /var/www/ad-mint-ai/backend/.env
sudo chown www-data:www-data /var/www/ad-mint-ai/backend/.env
```

---

## 📦 S3 Management

### List Frontend Files
```bash
aws s3 ls s3://ad-mint-ai-frontend/
```

### List Videos
```bash
aws s3 ls s3://ad-mint-ai-videos/
```

### Upload File to S3
```bash
aws s3 cp local-file.mp4 s3://ad-mint-ai-videos/
```

### Sync Directory
```bash
aws s3 sync local-dir/ s3://ad-mint-ai-frontend/ --delete
```

---

## 🐛 Troubleshooting

### Backend Not Starting
```bash
# Check logs
sudo journalctl -u fastapi -n 50 --no-pager

# Check if port is in use
sudo lsof -i :8000

# Test manually
cd /var/www/ad-mint-ai/backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Nginx Issues
```bash
# Test configuration
sudo nginx -t

# Check if site is enabled
ls -la /etc/nginx/sites-enabled/

# Verify FastAPI is running
curl http://127.0.0.1:8000/api/health
```

### Permission Issues
```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/ad-mint-ai/backend

# Fix permissions
sudo chmod -R 755 /var/www/ad-mint-ai
```

---

## 📍 Important Paths

- **Deployment**: `/var/www/ad-mint-ai`
- **Backend**: `/var/www/ad-mint-ai/backend`
- **Frontend Build**: `/var/www/ad-mint-ai/frontend/dist`
- **Environment**: `/var/www/ad-mint-ai/backend/.env`
- **Nginx Config**: `/etc/nginx/sites-available/ad-mint-ai`
- **Service File**: `/etc/systemd/system/fastapi.service`
- **Logs**: `/var/log/nginx/ad-mint-ai-*.log`

---

## 🌐 URLs

- **Frontend**: `http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`
- **Backend API**: `http://YOUR_EC2_IP/api/`
- **Health Check**: `http://YOUR_EC2_IP/api/health`

---

## ⚡ Quick Health Check

```bash
# One-liner to check everything
echo "FastAPI: $(curl -s -o /dev/null -w '%{http_code}' http://YOUR_EC2_IP/api/health)" && \
sudo systemctl is-active fastapi && \
sudo systemctl is-active nginx
```

---

For detailed instructions, see `DEPLOYMENT_STEPS.md`

