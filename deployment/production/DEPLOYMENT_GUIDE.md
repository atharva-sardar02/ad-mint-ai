# Ad Mint AI - Production Deployment Guide

This document provides a complete guide for deploying the Ad Mint AI application to AWS production environment.

## Table of Contents

1. [Infrastructure Overview](#infrastructure-overview)
2. [Prerequisites](#prerequisites)
3. [AWS Infrastructure Setup](#aws-infrastructure-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Database Setup](#database-setup)
7. [Configuration](#configuration)
8. [Verification](#verification)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Troubleshooting](#troubleshooting)

---

## Infrastructure Overview

### Architecture Components

- **EC2 Instance**: Backend API server (FastAPI + Nginx)
- **RDS PostgreSQL**: Production database
- **S3 Buckets**: 
  - `ad-mint-ai-frontend`: Frontend static website hosting
  - `ad-mint-ai-videos`: Video and thumbnail storage
- **VPC**: Default VPC with public/private subnets
- **Security Groups**: Network access control

### Service URLs

- **Frontend**: `http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`
- **Backend API**: `http://44.210.144.149/api/`
- **Health Check**: `http://44.210.144.149/api/health`

---

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured locally
3. **SSH Access** to EC2 instance
4. **GitHub Repository** access
5. **Environment Variables**:
   - OpenAI API Key
   - Replicate API Token
   - AWS Access Keys

---

## AWS Infrastructure Setup

### 1. S3 Buckets

#### Frontend Bucket (`ad-mint-ai-frontend`)

```powershell
# Create bucket
aws s3 mb s3://ad-mint-ai-frontend --region us-east-1

# Enable static website hosting
aws s3 website s3://ad-mint-ai-frontend/ --index-document index.html --error-document index.html

# Set public read policy
aws s3api put-bucket-policy --bucket ad-mint-ai-frontend --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::ad-mint-ai-frontend/*"
  }]
}'

# Configure CORS (allows all origins)
aws s3api put-bucket-cors --bucket ad-mint-ai-frontend --cors-configuration '{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }]
}'
```

**Website Endpoint**: `http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`

#### Videos Bucket (`ad-mint-ai-videos`)

```powershell
# Create bucket
aws s3 mb s3://ad-mint-ai-videos --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning --bucket ad-mint-ai-videos --versioning-configuration Status=Enabled

# Configure lifecycle policy (optional - for cost optimization)
aws s3api put-bucket-lifecycle-configuration --bucket ad-mint-ai-videos --lifecycle-configuration '{
  "Rules": [{
    "ID": "DeleteOldVersions",
    "Status": "Enabled",
    "NoncurrentVersionExpiration": {
      "NoncurrentDays": 30
    }
  }]
}'

# Configure CORS
aws s3api put-bucket-cors --bucket ad-mint-ai-videos --cors-configuration '{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }]
}'
```

### 2. EC2 Instance

#### Create Security Group

```powershell
# Get VPC ID
$vpcId = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text

# Create security group
aws ec2 create-security-group --group-name ad-mint-ai-ec2-sg --description "Security group for Ad Mint AI EC2 instance" --vpc-id $vpcId

# Allow HTTP (port 80)
aws ec2 authorize-security-group-ingress --group-name ad-mint-ai-ec2-sg --protocol tcp --port 80 --cidr 0.0.0.0/0

# Allow SSH (port 22)
aws ec2 authorize-security-group-ingress --group-name ad-mint-ai-ec2-sg --protocol tcp --port 22 --cidr 0.0.0.0/0
```

#### Launch EC2 Instance

```powershell
# Get latest Ubuntu 22.04 AMI
$amiId = aws ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=state,Values=available" --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" --output text

# Get subnet ID (public subnet)
$subnetId = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query "Subnets[0].SubnetId" --output text

# Create key pair (or use existing)
aws ec2 create-key-pair --key-name ad-mint-ai-key --query 'KeyMaterial' --output text > ad-mint-ai-key.pem

# Launch instance
aws ec2 run-instances --image-id $amiId --instance-type t3.medium --key-name ad-mint-ai-key --security-group-ids <SECURITY_GROUP_ID> --subnet-id $subnetId --associate-public-ip-address
```

**Note**: Save the key pair file securely. You'll need it for SSH access.

### 3. RDS PostgreSQL

#### Create DB Subnet Group

```powershell
# Get VPC ID
$vpcId = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text

# Get subnets (need at least 2 in different AZs)
$subnet1 = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query "Subnets[0].SubnetId" --output text
$subnet2 = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpcId" --query "Subnets[1].SubnetId" --output text

# Create DB subnet group
aws rds create-db-subnet-group --db-subnet-group-name ad-mint-ai-db-subnet-group --db-subnet-group-description "DB subnet group for Ad Mint AI RDS" --subnet-ids $subnet1 $subnet2
```

#### Create RDS Security Group

```powershell
# Get EC2 security group ID
$ec2SgId = aws ec2 describe-security-groups --filters "Name=group-name,Values=ad-mint-ai-ec2-sg" --query "SecurityGroups[0].GroupId" --output text

# Create RDS security group
aws ec2 create-security-group --group-name ad-mint-ai-rds-sg --description "Security group for Ad Mint AI RDS PostgreSQL" --vpc-id $vpcId

# Allow PostgreSQL (port 5432) from EC2
aws ec2 authorize-security-group-ingress --group-id <RDS_SG_ID> --protocol tcp --port 5432 --source-group $ec2SgId
```

#### Create RDS Instance

```powershell
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier ad-mint-ai-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.14 \
  --master-username ad_mint_user \
  --master-user-password <SECURE_PASSWORD> \
  --db-name ad_mint_ai \
  --allocated-storage 20 \
  --storage-type gp3 \
  --db-subnet-group-name ad-mint-ai-db-subnet-group \
  --vpc-security-group-ids <RDS_SG_ID> \
  --backup-retention-period 7 \
  --no-publicly-accessible
```

**Note**: This takes 10-15 minutes. Wait for status to be "available".

**Get RDS Endpoint**:
```powershell
aws rds describe-db-instances --db-instance-identifier ad-mint-ai-db --query "DBInstances[0].Endpoint.Address" --output text
```

---

## Backend Deployment

### 1. Connect to EC2 Instance

```bash
ssh -i ad-mint-ai-key.pem ubuntu@<EC2_PUBLIC_IP>
```

### 2. Install Dependencies

```bash
# Update system
sudo apt update

# Install Python and dependencies
sudo apt install -y python3.10-venv python3-pip

# Install Nginx
sudo apt install -y nginx

# Install PostgreSQL client
sudo apt install -y postgresql-client

# Install OpenCV dependencies
sudo apt install -y libgl1-mesa-glx libglib2.0-0
```

### 3. Deploy Backend Code

```bash
# Create application directory
sudo mkdir -p /var/www/ad-mint-ai
sudo chown ubuntu:ubuntu /var/www/ad-mint-ai

# Clone repository (or copy files)
cd /var/www/ad-mint-ai
git clone https://github.com/atharva-sardar02/ad-mint-ai.git .

# Or copy backend folder via SCP
# scp -r backend/ ubuntu@<EC2_IP>:/var/www/ad-mint-ai/
```

### 4. Set Up Python Environment

```bash
cd /var/www/ad-mint-ai/backend

# Create virtual environment
python3 -m venv venv

# Install dependencies
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Install PostgreSQL adapter
venv/bin/pip install psycopg2-binary
```

### 5. Configure Environment Variables

Create `/var/www/ad-mint-ai/backend/.env`:

```bash
cat > /var/www/ad-mint-ai/backend/.env << 'EOF'
DATABASE_URL=postgresql://ad_mint_user:<PASSWORD>@<RDS_ENDPOINT>:5432/ad_mint_ai
SECRET_KEY=<GENERATE_SECURE_KEY>
CORS_ALLOWED_ORIGINS=*
DEBUG=False
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# OpenAI API Key
OPENAI_API_KEY=<YOUR_OPENAI_KEY>

# Replicate API Token
REPLICATE_API_TOKEN=<YOUR_REPLICATE_TOKEN>

# AWS S3 Configuration
STORAGE_MODE=s3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<YOUR_AWS_ACCESS_KEY>
AWS_SECRET_ACCESS_KEY=<YOUR_AWS_SECRET_KEY>
AWS_S3_VIDEO_BUCKET=ad-mint-ai-videos
EOF
```

**Important**: Replace all `<PLACEHOLDERS>` with actual values.

### 6. Configure Nginx

Create `/etc/nginx/sites-available/ad-mint-ai`:

```nginx
# Nginx configuration for Ad Mint AI
server {
    listen 80;
    server_name _;

    access_log /var/log/nginx/ad-mint-ai-access.log;
    error_log /var/log/nginx/ad-mint-ai-error.log;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
    }

    location /api/health {
        proxy_pass http://127.0.0.1:8000/api/health;
        access_log off;
        proxy_set_header Host $host;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable and test:

```bash
# Enable site
sudo ln -sf /etc/nginx/sites-available/ad-mint-ai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 7. Create Systemd Service

Create `/etc/systemd/system/fastapi.service`:

```ini
[Unit]
Description=Ad Mint AI FastAPI Application
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/ad-mint-ai/backend
Environment="PATH=/var/www/ad-mint-ai/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=-/var/www/ad-mint-ai/backend/.env
ExecStart=/var/www/ad-mint-ai/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
StandardOutput=journal
StandardError=journal
SyslogIdentifier=fastapi

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
# Create log directory
sudo mkdir -p /var/log/fastapi
sudo chown www-data:www-data /var/log/fastapi

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable fastapi
sudo systemctl start fastapi

# Check status
sudo systemctl status fastapi
```

### 8. Initialize Database

```bash
cd /var/www/ad-mint-ai/backend
venv/bin/python -m app.db.init_db
```

---

## Frontend Deployment

### 1. Build Frontend with Production API URL

```powershell
cd frontend
$env:VITE_API_URL="http://<EC2_PUBLIC_IP>"
npm run build
```

### 2. Upload to S3

```powershell
aws s3 sync frontend/dist/ s3://ad-mint-ai-frontend/ --delete
```

**Frontend URL**: `http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`

---

## Database Setup

### 1. Test RDS Connection

```bash
# From EC2 instance
psql -h <RDS_ENDPOINT> -U ad_mint_user -d ad_mint_ai -c "SELECT version();"
```

### 2. Initialize Database Tables

```bash
cd /var/www/ad-mint-ai/backend
venv/bin/python -m app.db.init_db
```

---

## Configuration

### Environment Variables Summary

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | JWT secret key | Random 32+ character string |
| `STORAGE_MODE` | Storage backend | `s3` or `local` |
| `AWS_S3_VIDEO_BUCKET` | S3 bucket for videos | `ad-mint-ai-videos` |
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `REPLICATE_API_TOKEN` | Replicate API token | `r8_...` |

### Service Management

```bash
# FastAPI service
sudo systemctl status fastapi
sudo systemctl restart fastapi
sudo journalctl -u fastapi -f

# Nginx service
sudo systemctl status nginx
sudo systemctl restart nginx
sudo nginx -t
```

---

## Verification

### 1. Check Backend Health

```bash
curl http://<EC2_PUBLIC_IP>/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "database": {"status": "healthy", "type": "postgresql"},
    "storage": {"status": "healthy", "type": "s3"},
    "external_apis": {...}
  }
}
```

### 2. Check Frontend

Open in browser: `http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`

### 3. Test Video Generation

1. Register/Login via frontend
2. Create a video generation request
3. Verify video is uploaded to S3
4. Check video playback

---

## Troubleshooting

### Backend Not Starting

```bash
# Check service logs
sudo journalctl -u fastapi -n 50 --no-pager

# Common issues:
# - Missing dependencies: Check import errors
# - Database connection: Verify DATABASE_URL
# - S3 connection: Check AWS credentials
# - Permission errors: Check file ownership
```

### Nginx 404 Errors

```bash
# Check Nginx error logs
sudo tail -f /var/log/nginx/ad-mint-ai-error.log

# Verify FastAPI is running
curl http://127.0.0.1:8000/api/health

# Test Nginx configuration
sudo nginx -t
```

### Database Connection Issues

```bash
# Test connection
psql -h <RDS_ENDPOINT> -U ad_mint_user -d ad_mint_ai

# Check security group rules
# Verify RDS is in same VPC as EC2
# Check security group allows port 5432 from EC2 SG
```

### S3 Upload Failures

```bash
# Check AWS credentials in .env
# Verify bucket exists and is accessible
# Check IAM permissions
# Verify bucket name matches AWS_S3_VIDEO_BUCKET
```

### Frontend Not Connecting to Backend

```bash
# Verify VITE_API_URL in build
# Check browser console for CORS errors
# Verify backend is accessible from internet
# Check security group allows HTTP (port 80)
```

---

## Important URLs and Credentials

### Production URLs

- **Frontend**: `http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`
- **Backend API**: `http://44.210.144.149/api/`
- **Health Check**: `http://44.210.144.149/api/health`

### AWS Resources

- **EC2 Instance**: `i-031c81da0e0986f2e` (IP: `44.210.144.149`)
- **RDS Instance**: `ad-mint-ai-db` (Endpoint: `ad-mint-ai-db.crws0amqe1e3.us-east-1.rds.amazonaws.com`)
- **S3 Frontend**: `ad-mint-ai-frontend`
- **S3 Videos**: `ad-mint-ai-videos`
- **VPC**: `vpc-03cd6462b46350c8e`
- **EC2 Security Group**: `sg-0b450f9ac038263ea`
- **RDS Security Group**: `sg-02a861ff2ac9629ab`

### Database Credentials

- **Username**: `ad_mint_user`
- **Database**: `ad_mint_ai`
- **Port**: `5432`
- **Password**: (stored in `.env` file)

---

## Maintenance

### Updating Backend

```bash
# SSH to EC2
ssh -i ad-mint-ai-key.pem ubuntu@<EC2_IP>

# Pull latest code
cd /var/www/ad-mint-ai
git pull

# Restart service
sudo systemctl restart fastapi
```

### Updating Frontend

```powershell
# Build with production API URL
cd frontend
$env:VITE_API_URL="http://<EC2_IP>"
npm run build

# Upload to S3
aws s3 sync frontend/dist/ s3://ad-mint-ai-frontend/ --delete
```

### Database Backups

RDS automated backups are enabled with 7-day retention. Manual snapshots:

```powershell
aws rds create-db-snapshot --db-instance-identifier ad-mint-ai-db --db-snapshot-identifier ad-mint-ai-manual-$(Get-Date -Format "yyyyMMdd")
```

---

## CI/CD Pipeline

### Automatic Deployment

The project includes a GitHub Actions workflow (`.github/workflows/deploy.yml`) that automatically deploys both frontend and backend to production when code is pushed to the `main` branch.

#### How It Works

1. **Trigger**: Push to `main` branch or manual workflow dispatch
2. **Frontend Deployment**:
   - Builds frontend with production API URL (`http://44.210.144.149`)
   - Uploads to S3 bucket `ad-mint-ai-frontend`
   - Verifies deployment success
3. **Backend Deployment**:
   - Creates backup of current deployment
   - Pulls latest code from GitHub
   - Updates Python dependencies
   - Restarts FastAPI service
   - Performs health check (polls `/api/health` for up to 60 seconds)
   - Automatically rolls back if health check fails

#### Required GitHub Secrets

Configure the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

| Secret Name | Description | Example |
|------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 deployment | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 deployment | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `EC2_USERNAME` | SSH username for EC2 instance | `ubuntu` |
| `EC2_SSH_KEY` | **Complete private key content** from `.pem` file | Copy entire contents of `ad-mint-ai-key.pem` |

**Important Notes:**
- `EC2_SSH_KEY` should contain the **entire private key file content** (including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`)
- Never commit private keys to the repository
- The `.env` file on EC2 is **not modified** by the CI/CD pipeline (it remains as configured manually)
- **Database migrations** are run automatically during deployment (all migrations in `backend/app/db/migrations/`)

#### Setting Up GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact name listed above
5. For `EC2_SSH_KEY`, open your `.pem` file and copy the entire contents (including headers)

#### Deployment Process

The workflow performs the following steps:

1. **Checkout code** from GitHub
2. **Configure AWS credentials** using secrets
3. **Setup SSH key** for EC2 access
4. **Build frontend** with `VITE_API_URL=http://44.210.144.149`
5. **Deploy frontend** to S3 with `--delete` flag (removes old files)
6. **Verify frontend** deployment (checks for `index.html`)
7. **Backup backend** (copies `/var/www/ad-mint-ai` to `/var/www/ad-mint-ai.backup`)
8. **Deploy backend**:
   - Pull latest code: `git reset --hard origin/main`
   - Update dependencies: `pip install -r requirements.txt`
   - Run database migrations: `python -m app.db.migrations.run_all`
   - Restart service: `sudo systemctl restart fastapi`
9. **Health check**: Polls `/api/health` every 5 seconds for up to 60 seconds
10. **Rollback** (if health check fails):
    - Restore from backup
    - Restart service
    - Fail workflow with error message

#### Manual Deployment

You can also trigger the workflow manually:

1. Go to **Actions** tab in GitHub
2. Select **Deploy to Production** workflow
3. Click **Run workflow**
4. Select branch (usually `main`)
5. Click **Run workflow**

#### Monitoring Deployments

- View deployment status in GitHub Actions tab
- Check deployment logs for detailed output
- Monitor health endpoint: `http://44.210.144.149/api/health`
- View service logs on EC2: `sudo journalctl -u fastapi -f`

#### Rollback

If a deployment fails the health check:
- Automatic rollback restores the previous version
- Backup directory is preserved for manual recovery
- Service is restarted with previous code
- Workflow fails with clear error message

To manually rollback:
```bash
ssh -i ad-mint-ai-key.pem ubuntu@44.210.144.149
cd /var/www/ad-mint-ai.backup
# Follow rollback script: deployment/scripts/rollback.sh
```

---

## Security Notes

⚠️ **Important Security Considerations**:

1. **No SSL/TLS**: Current deployment uses HTTP only (as per architecture requirements)
2. **No Rate Limiting**: Rate limiting has been removed (as per architecture requirements)
3. **CORS**: Configured to allow all origins (as per architecture requirements)
4. **Database**: RDS is in private subnet, not publicly accessible
5. **Credentials**: Store `.env` file securely, never commit to git

---

## Cost Optimization

- **EC2**: Use `t3.medium` or smaller for development
- **RDS**: Use `db.t3.micro` for development
- **S3**: Enable lifecycle policies to delete old versions
- **Backups**: Adjust RDS backup retention period as needed

---

## Support

For issues or questions:
1. Check service logs: `sudo journalctl -u fastapi -f`
2. Check Nginx logs: `sudo tail -f /var/log/nginx/ad-mint-ai-error.log`
3. Verify health endpoint: `curl http://<EC2_IP>/api/health`
4. Review this deployment guide

---

**Last Updated**: November 16, 2025  
**Deployment Status**: ✅ Production Ready


