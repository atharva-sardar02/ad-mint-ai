# Production Deployment Guide

This guide covers the complete production deployment setup for Ad Mint AI.

## Prerequisites

- AWS account with appropriate permissions
- EC2 instance (Ubuntu 22.04 LTS, t3.large or t3.xlarge)
- AWS RDS PostgreSQL instance
- Domain name (optional but recommended)
- AWS CLI installed and configured
- SSH access to EC2 instance

## Architecture Overview

- **Frontend**: S3 bucket `ad-mint-ai-frontend` with static website hosting
- **Backend**: EC2 instance at `/var/www/ad-mint-ai/backend/`
- **Database**: AWS RDS PostgreSQL in private subnet
- **Storage**: S3 bucket `ad-mint-ai-videos` for video files
- **Nginx**: Reverse proxies `/api/*` requests to FastAPI (no frontend serving)

## Step-by-Step Deployment

### 1. S3 Frontend Setup

```bash
# Run the S3 frontend setup script
cd deployment
chmod +x setup-s3-frontend.sh
./setup-s3-frontend.sh us-east-1

# Build and upload frontend
cd ../frontend
npm run build
aws s3 sync dist/ s3://ad-mint-ai-frontend/ --delete
```

### 2. S3 Video Storage Setup

```bash
# Run the S3 video storage setup script
cd deployment
chmod +x setup-s3-videos.sh
./setup-s3-videos.sh us-east-1
```

### 3. EC2 Backend Deployment

```bash
# SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Run deployment script
cd /var/www/ad-mint-ai
sudo ./deployment/deploy.sh
```

### 4. Environment Variables

Create `/var/www/ad-mint-ai/backend/.env` with production values:

```bash
sudo nano /var/www/ad-mint-ai/backend/.env
```

Required variables:
- `DATABASE_URL` (RDS endpoint: `postgresql://user:pass@xxx.rds.amazonaws.com:5432/dbname`)
- `SECRET_KEY` (strong random string)
- `OPENAI_API_KEY`
- `REPLICATE_API_TOKEN`
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (or use IAM role)
- `AWS_S3_VIDEO_BUCKET=ad-mint-ai-videos`
- `STORAGE_MODE=s3`
- `CORS_ALLOWED_ORIGINS` (not used - CORS allows all origins)

Set proper permissions:
```bash
sudo chmod 600 /var/www/ad-mint-ai/backend/.env
sudo chown www-data:www-data /var/www/ad-mint-ai/backend/.env
```

### 5. Domain and DNS Configuration

- **Frontend**: CNAME record pointing to S3 website endpoint
- **API**: A record pointing to EC2 public IP

CORS allows all origins (no configuration needed).

### 6. Basic Networking

- Configure EC2 security group (ports 80, 22 only)
- Configure RDS security group (port 5432 from EC2 only)

### 7. Monitoring and Logging

Log files:
- FastAPI: `/var/log/fastapi/app.log`
- Nginx access: `/var/log/nginx/ad-mint-ai-access.log`
- Nginx error: `/var/log/nginx/ad-mint-ai-error.log`

Health check endpoint: `GET /api/health`

## Troubleshooting

See `TROUBLESHOOTING.md` for common issues and solutions.

## Rollback Procedure

See `ROLLBACK.md` for rollback procedures.

