# Deployment Checklist

Use this checklist to deploy Ad Mint AI to production.

## Pre-Deployment Prerequisites

- [ ] AWS account with appropriate permissions
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] EC2 instance launched (Ubuntu 22.04 LTS, t3.large or t3.xlarge)
- [ ] EC2 security group configured (ports 80, 22 open)
- [ ] SSH key pair for EC2 access
- [ ] Domain name (optional)

## Step 1: AWS Infrastructure Setup

### 1.1 S3 Frontend Bucket
```bash
cd deployment
chmod +x setup-s3-frontend.sh
./setup-s3-frontend.sh us-east-1
```
- [ ] S3 bucket `ad-mint-ai-frontend` created
- [ ] Static website hosting enabled
- [ ] Bucket policy configured
- [ ] CORS configured

### 1.2 S3 Video Storage Bucket
```bash
chmod +x setup-s3-videos.sh
./setup-s3-videos.sh us-east-1
```
- [ ] S3 bucket `ad-mint-ai-videos` created
- [ ] Versioning enabled
- [ ] Lifecycle policies configured
- [ ] CORS configured

### 1.3 RDS Database (Optional - can use SQLite for MVP)
```bash
chmod +x setup-rds.sh
./setup-rds.sh us-east-1
```
- [ ] RDS PostgreSQL instance created
- [ ] Security group configured
- [ ] Database credentials saved
- [ ] Connection string ready

## Step 2: Frontend Deployment

```bash
cd frontend
npm install
npm run build
aws s3 sync dist/ s3://ad-mint-ai-frontend/ --delete
```

- [ ] Frontend built successfully
- [ ] Frontend uploaded to S3
- [ ] Frontend accessible via S3 website endpoint

## Step 3: Backend Deployment

### 3.1 Connect to EC2
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 3.2 Prepare EC2 Instance
```bash
# Create deployment directory
sudo mkdir -p /var/www/ad-mint-ai
sudo chown ubuntu:ubuntu /var/www/ad-mint-ai

# Clone repository or upload files
cd /var/www/ad-mint-ai
git clone https://github.com/your-org/ad-mint-ai.git .
# OR use scp/rsync to upload files
```

### 3.3 Run Deployment Script
```bash
cd /var/www/ad-mint-ai
chmod +x deployment/deploy.sh
sudo ./deployment/deploy.sh /var/www/ad-mint-ai
```

- [ ] System dependencies installed
- [ ] Python virtual environment created
- [ ] Backend dependencies installed
- [ ] Nginx configured
- [ ] Systemd service created
- [ ] Services started

### 3.4 Configure Environment Variables
```bash
sudo nano /var/www/ad-mint-ai/backend/.env
```

Required variables:
- `DATABASE_URL` (RDS endpoint or SQLite path)
- `SECRET_KEY` (generate with: `openssl rand -hex 32`)
- `OPENAI_API_KEY`
- `REPLICATE_API_TOKEN`
- `AWS_ACCESS_KEY_ID` (or use IAM role)
- `AWS_SECRET_ACCESS_KEY` (or use IAM role)
- `AWS_S3_VIDEO_BUCKET=ad-mint-ai-videos`
- `STORAGE_MODE=s3`
- `CORS_ALLOWED_ORIGINS` (not used - CORS allows all)

Set permissions:
```bash
sudo chmod 600 /var/www/ad-mint-ai/backend/.env
sudo chown www-data:www-data /var/www/ad-mint-ai/backend/.env
```

- [ ] `.env` file created
- [ ] All environment variables set
- [ ] File permissions configured

### 3.5 Restart Services
```bash
sudo systemctl restart fastapi
sudo systemctl restart nginx
sudo systemctl status fastapi
```

- [ ] FastAPI service running
- [ ] Nginx service running

## Step 4: Verification

### 4.1 Health Check
```bash
curl http://your-ec2-ip/api/health
```

- [ ] Health endpoint returns 200
- [ ] Database connectivity OK
- [ ] S3 connectivity OK (if using S3)

### 4.2 Frontend Access
- [ ] Frontend loads from S3 website endpoint
- [ ] Frontend can make API requests

### 4.3 Test API Endpoints
```bash
# Test root endpoint
curl http://your-ec2-ip/api/

# Test health endpoint
curl http://your-ec2-ip/api/health
```

- [ ] API endpoints accessible
- [ ] CORS working (all origins allowed)

## Step 5: DNS Configuration (Optional)

- [ ] Frontend DNS configured (CNAME to S3 website endpoint)
- [ ] API DNS configured (A record to EC2 IP)
- [ ] DNS propagation verified

## Post-Deployment

- [ ] Monitor logs: `sudo journalctl -u fastapi -f`
- [ ] Check Nginx logs: `sudo tail -f /var/log/nginx/ad-mint-ai-access.log`
- [ ] Verify video generation works
- [ ] Test user authentication
- [ ] Verify S3 video uploads

## Troubleshooting

See `deployment/production/TROUBLESHOOTING.md` for common issues.

## Quick Commands

```bash
# Check service status
sudo systemctl status fastapi
sudo systemctl status nginx

# View logs
sudo journalctl -u fastapi -f
sudo tail -f /var/log/fastapi/app.log
sudo tail -f /var/log/nginx/ad-mint-ai-error.log

# Restart services
sudo systemctl restart fastapi
sudo systemctl restart nginx

# Test database connection
psql $DATABASE_URL

# Test S3 connection
aws s3 ls s3://ad-mint-ai-videos/
```

