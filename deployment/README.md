# Deployment Guide for Ad Mint AI

This guide provides step-by-step instructions for deploying the Ad Mint AI application to an AWS EC2 instance running Ubuntu 22.04 LTS.

## Table of Contents

- [Prerequisites](#prerequisites)
- [EC2 Instance Setup](#ec2-instance-setup)
- [Initial Deployment](#initial-deployment)
- [Environment Configuration](#environment-configuration)
- [Post-Deployment Verification](#post-deployment-verification)
- [Troubleshooting](#troubleshooting)
- [Service Management](#service-management)

## Prerequisites

### EC2 Instance Requirements

- **OS:** Ubuntu 22.04 LTS
- **Minimum Specs:**
  - 2 vCPU
  - 4 GB RAM
  - 20 GB storage
- **Network:** EC2 instance must have:
  - Public IP address (or configured via Elastic IP)
  - Security group allowing:
    - SSH (port 22) from your IP
    - HTTP (port 80) from anywhere (0.0.0.0/0)
    - HTTPS (port 443) from anywhere (optional, for SSL)
    - Custom TCP (port 8000) from localhost only (for FastAPI)

### AWS RDS PostgreSQL (Optional for MVP)

If using PostgreSQL instead of SQLite:
- AWS RDS PostgreSQL instance in the same VPC/subnet as EC2
- Security group allowing EC2 instance to connect on port 5432
- Database name, username, and password

### Local Requirements

- SSH access to EC2 instance
- Git installed locally
- Basic knowledge of Linux command line

## EC2 Instance Setup

### 1. Launch EC2 Instance

1. Log in to AWS Console
2. Navigate to EC2 → Launch Instance
3. Select Ubuntu Server 22.04 LTS
4. Choose instance type (t3.small or larger recommended)
5. Configure security group as specified in Prerequisites
6. Create or select a key pair for SSH access
7. Launch instance

### 2. Connect to EC2 Instance

```bash
# Replace with your key file and instance IP
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 3. Prepare Deployment Directory

```bash
# Create deployment directory
sudo mkdir -p /var/www/ad-mint-ai
sudo chown ubuntu:ubuntu /var/www/ad-mint-ai

# Clone repository (or upload files)
cd /var/www/ad-mint-ai
git clone https://github.com/your-org/ad-mint-ai.git .
# OR: Use scp/rsync to upload files
```

## Initial Deployment

### Automated Deployment (Recommended)

The deployment script automates all setup steps:

```bash
# Make script executable
chmod +x deployment/deploy.sh

# Run deployment script (requires sudo)
sudo ./deployment/deploy.sh /var/www/ad-mint-ai
```

The script will:
1. Install system dependencies (Python 3.11, Node.js 18+, FFmpeg, Nginx)
2. Set up Python virtual environment
3. Install Python dependencies
4. Build React frontend
5. Configure Nginx
6. Create systemd service for FastAPI
7. Start all services
8. Initialize database
9. Verify deployment

### Manual Deployment

If you prefer manual setup, follow these steps:

#### 1. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo bash -
sudo apt-get install -y nodejs
sudo apt-get install -y ffmpeg nginx
```

#### 2. Set Up Python Virtual Environment

```bash
cd /var/www/ad-mint-ai/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

#### 3. Build Frontend

```bash
cd /var/www/ad-mint-ai/frontend
npm install
npm run build
```

#### 4. Configure Nginx

```bash
# Copy and update Nginx configuration
sudo cp deployment/nginx.conf /etc/nginx/sites-available/ad-mint-ai
sudo sed -i "s|/path/to/ad-mint-ai|/var/www/ad-mint-ai|g" /etc/nginx/sites-available/ad-mint-ai
sudo sed -i "s|server_name _;|server_name your-domain.com;|g" /etc/nginx/sites-available/ad-mint-ai

# Enable site
sudo ln -s /etc/nginx/sites-available/ad-mint-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. Configure Systemd Service

```bash
# Copy and update service file
sudo cp deployment/fastapi.service /etc/systemd/system/fastapi.service
sudo sed -i "s|/path/to/ad-mint-ai|/var/www/ad-mint-ai|g" /etc/systemd/system/fastapi.service
sudo sed -i "s|/path/to/venv|/var/www/ad-mint-ai/backend/venv|g" /etc/systemd/system/fastapi.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable fastapi.service
sudo systemctl start fastapi.service
```

#### 6. Initialize Database

```bash
cd /var/www/ad-mint-ai/backend
source venv/bin/activate
python -m app.db.init_db
deactivate
```

## Environment Configuration

### Backend Environment Variables

1. Copy the example file:
   ```bash
   cd /var/www/ad-mint-ai/backend
   cp .env.example .env
   ```

2. Edit `.env` with your actual values:
   ```bash
   nano .env
   ```

3. Required variables:
   - `DATABASE_URL`: PostgreSQL connection string (or SQLite for dev)
   - `SECRET_KEY`: Secure random string (generate with `openssl rand -hex 32`)
   - `CORS_ALLOWED_ORIGINS`: Your domain(s), comma-separated

4. Optional variables:
   - `OPENAI_API_KEY`: For LLM enhancement features
   - `REPLICATE_API_TOKEN`: For video generation
   - `DEBUG`: Set to `False` for production

### Frontend Environment Variables

1. Copy the example file:
   ```bash
   cd /var/www/ad-mint-ai/frontend
   cp .env.example .env
   ```

2. Edit `.env` with your API URL:
   ```bash
   nano .env
   ```

3. Set `VITE_API_URL` to your backend URL (e.g., `http://your-ec2-ip` or `https://api.yourdomain.com`)

4. Rebuild frontend after changing environment variables:
   ```bash
   npm run build
   sudo systemctl reload nginx
   ```

## Post-Deployment Verification

### 1. Check Service Status

```bash
# Check FastAPI service
sudo systemctl status fastapi

# Check Nginx service
sudo systemctl status nginx
```

### 2. Test Health Endpoint

```bash
# From EC2 instance
curl http://127.0.0.1:8000/api/health

# From your local machine
curl http://your-ec2-ip/api/health
```

Expected response: `{"status":"healthy"}`

### 3. Verify Frontend

1. Open browser and navigate to `http://your-ec2-ip`
2. You should see the React application
3. Check browser console for any errors

### 4. Verify API Proxy

```bash
# Test API endpoint through Nginx
curl http://your-ec2-ip/api/health
```

### 5. Check Logs

```bash
# FastAPI logs
sudo journalctl -u fastapi -f

# Nginx access logs
sudo tail -f /var/log/nginx/ad-mint-ai-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/ad-mint-ai-error.log
```

## Troubleshooting

### FastAPI Service Not Starting

1. Check service status:
   ```bash
   sudo systemctl status fastapi
   ```

2. View detailed logs:
   ```bash
   sudo journalctl -u fastapi -n 50
   ```

3. Common issues:
   - **Port 8000 already in use:** Check with `sudo lsof -i :8000`
   - **Virtual environment path incorrect:** Verify paths in `/etc/systemd/system/fastapi.service`
   - **Missing dependencies:** Activate venv and run `pip install -r requirements.txt`
   - **Database connection error:** Check `DATABASE_URL` in `.env` file

### Nginx Not Serving Frontend

1. Test Nginx configuration:
   ```bash
   sudo nginx -t
   ```

2. Check if site is enabled:
   ```bash
   ls -la /etc/nginx/sites-enabled/
   ```

3. Verify frontend build exists:
   ```bash
   ls -la /var/www/ad-mint-ai/frontend/dist/
   ```

4. Check Nginx error logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

### API Requests Not Proxying

1. Verify Nginx configuration has correct proxy_pass:
   ```bash
   sudo grep -A 5 "location /api/" /etc/nginx/sites-available/ad-mint-ai
   ```

2. Test backend directly:
   ```bash
   curl http://127.0.0.1:8000/api/health
   ```

3. Check FastAPI service is running:
   ```bash
   sudo systemctl status fastapi
   ```

### Database Connection Issues

1. For PostgreSQL:
   - Verify RDS security group allows EC2 instance
   - Test connection: `psql -h your-rds-endpoint -U username -d database`
   - Check `DATABASE_URL` format: `postgresql://user:password@host:port/dbname`

2. For SQLite:
   - Check file permissions: `ls -la backend/ad_mint_ai.db`
   - Ensure www-data user can write to backend directory

## Service Management

### FastAPI Service

```bash
# Start service
sudo systemctl start fastapi

# Stop service
sudo systemctl stop fastapi

# Restart service
sudo systemctl restart fastapi

# View logs
sudo journalctl -u fastapi -f

# Check status
sudo systemctl status fastapi
```

### Nginx Service

```bash
# Reload configuration (no downtime)
sudo systemctl reload nginx

# Restart service
sudo systemctl restart nginx

# Test configuration
sudo nginx -t

# View logs
sudo tail -f /var/log/nginx/ad-mint-ai-error.log
```

### Updating Application

1. Pull latest changes:
   ```bash
   cd /var/www/ad-mint-ai
   git pull
   ```

2. Update backend:
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt
   python -m app.db.init_db  # If schema changed
   deactivate
   sudo systemctl restart fastapi
   ```

3. Update frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   sudo systemctl reload nginx
   ```

## Security Considerations

1. **Firewall:** Configure UFW or AWS Security Groups to restrict access
2. **SSL/TLS:** Set up Let's Encrypt certificate for HTTPS (recommended)
3. **Secrets:** Never commit `.env` files to version control
4. **Updates:** Regularly update system packages: `sudo apt-get update && sudo apt-get upgrade`
5. **Backups:** Set up regular database backups for production

## Next Steps

- Configure domain name and DNS
- Set up SSL certificate (Let's Encrypt)
- Configure monitoring and alerting
- Set up automated backups
- Configure CI/CD pipeline for deployments

## Support

For issues or questions:
- Check logs: `sudo journalctl -u fastapi -f`
- Review this documentation
- Check GitHub issues
- Contact development team


