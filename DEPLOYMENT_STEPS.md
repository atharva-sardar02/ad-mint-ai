# Production Deployment Steps - Ad Mint AI

Complete step-by-step guide to deploy your webapp to production.

## Prerequisites

Before starting, ensure you have:
- ✅ AWS account with appropriate permissions
- ✅ AWS CLI installed and configured (`aws configure`)
- ✅ SSH key pair for EC2 access
- ✅ GitHub repository access
- ✅ Environment variables ready (OpenAI API key, Replicate token, AWS credentials)

---

## Step 1: AWS Infrastructure Setup

### 1.1 Create S3 Frontend Bucket

```bash
# Create bucket
aws s3 mb s3://ad-mint-ai-frontend --region us-east-1

# Enable static website hosting
aws s3 website s3://ad-mint-ai-frontend/ \
  --index-document index.html \
  --error-document index.html

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

# Configure CORS
aws s3api put-bucket-cors --bucket ad-mint-ai-frontend --cors-configuration '{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }]
}'
```

**Note**: Your frontend will be accessible at: `http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`

### 1.2 Create S3 Videos Bucket

```bash
# Create bucket
aws s3 mb s3://ad-mint-ai-videos --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ad-mint-ai-videos \
  --versioning-configuration Status=Enabled

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

### 1.3 Launch EC2 Instance

```bash
# Get VPC ID (default VPC)
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text)

# Create security group
SG_ID=$(aws ec2 create-security-group \
  --group-name ad-mint-ai-ec2-sg \
  --description "Security group for Ad Mint AI EC2 instance" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

# Allow HTTP (port 80)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow SSH (port 22) - replace with your IP for better security
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# Get latest Ubuntu 22.04 AMI
AMI_ID=$(aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=state,Values=available" \
  --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" \
  --output text)

# Get subnet ID
SUBNET_ID=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[0].SubnetId" --output text)

# Create key pair (if you don't have one)
aws ec2 create-key-pair \
  --key-name ad-mint-ai-key \
  --query 'KeyMaterial' \
  --output text > ad-mint-ai-key.pem

# Set proper permissions
chmod 400 ad-mint-ai-key.pem

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.medium \
  --key-name ad-mint-ai-key \
  --security-group-ids $SG_ID \
  --subnet-id $SUBNET_ID \
  --associate-public-ip-address \
  --query 'Instances[0].InstanceId' \
  --output text)

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
EC2_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "EC2 Instance IP: $EC2_IP"
echo "Save this IP - you'll need it for deployment!"
```

**Save the EC2 IP address** - you'll need it for the next steps.

### 1.4 (Optional) Set Up RDS PostgreSQL

If you want to use PostgreSQL instead of SQLite:

```bash
# Get VPC and subnet IDs
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text)
SUBNET1=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[0].SubnetId" --output text)
SUBNET2=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[1].SubnetId" --output text)

# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name ad-mint-ai-db-subnet-group \
  --db-subnet-group-description "DB subnet group for Ad Mint AI RDS" \
  --subnet-ids $SUBNET1 $SUBNET2

# Get EC2 security group ID
EC2_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=ad-mint-ai-ec2-sg" --query "SecurityGroups[0].GroupId" --output text)

# Create RDS security group
RDS_SG_ID=$(aws ec2 create-security-group \
  --group-name ad-mint-ai-rds-sg \
  --description "Security group for Ad Mint AI RDS PostgreSQL" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

# Allow PostgreSQL from EC2
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group $EC2_SG_ID

# Create RDS instance (takes 10-15 minutes)
aws rds create-db-instance \
  --db-instance-identifier ad-mint-ai-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.14 \
  --master-username ad_mint_user \
  --master-user-password "YOUR_SECURE_PASSWORD_HERE" \
  --db-name ad_mint_ai \
  --allocated-storage 20 \
  --storage-type gp3 \
  --db-subnet-group-name ad-mint-ai-db-subnet-group \
  --vpc-security-group-ids $RDS_SG_ID \
  --backup-retention-period 7 \
  --no-publicly-accessible

# Get RDS endpoint (wait for instance to be available first)
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier ad-mint-ai-db \
  --query "DBInstances[0].Endpoint.Address" \
  --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"
```

---

## Step 2: Backend Deployment

### 2.1 Connect to EC2 Instance

```bash
# Replace with your EC2 IP and key file path
ssh -i ad-mint-ai-key.pem ubuntu@YOUR_EC2_IP
```

### 2.2 Prepare Deployment Directory

```bash
# Create deployment directory
sudo mkdir -p /var/www/ad-mint-ai
sudo chown ubuntu:ubuntu /var/www/ad-mint-ai

# Clone repository
cd /var/www/ad-mint-ai
git clone https://github.com/YOUR_USERNAME/ad-mint-ai.git .

# OR if you prefer to upload files manually:
# Exit SSH and from your local machine:
# scp -r -i ad-mint-ai-key.pem backend/ ubuntu@YOUR_EC2_IP:/var/www/ad-mint-ai/
```

### 2.3 Run Automated Deployment Script

```bash
# Make script executable
chmod +x deployment/deploy.sh

# Run deployment (requires sudo)
sudo ./deployment/deploy.sh /var/www/ad-mint-ai
```

The script will automatically:
- Install system dependencies (Python 3.11, Node.js, FFmpeg, Nginx)
- Set up Python virtual environment
- Install Python dependencies
- Build React frontend
- Configure Nginx
- Create systemd service
- Start all services
- Initialize database

### 2.4 Configure Environment Variables

```bash
# Create .env file
sudo nano /var/www/ad-mint-ai/backend/.env
```

Add the following content (replace placeholders with actual values):

```bash
# Database (use SQLite for MVP or PostgreSQL for production)
DATABASE_URL=sqlite:///./ad_mint_ai.db
# OR for PostgreSQL:
# DATABASE_URL=postgresql://ad_mint_user:PASSWORD@RDS_ENDPOINT:5432/ad_mint_ai

# Security
SECRET_KEY=$(openssl rand -hex 32)  # Generate this on the server
CORS_ALLOWED_ORIGINS=*
DEBUG=False
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-key-here

# Replicate API Token
REPLICATE_API_TOKEN=r8_your-replicate-token-here

# AWS S3 Configuration
STORAGE_MODE=s3
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_VIDEO_BUCKET=ad-mint-ai-videos
```

**Generate SECRET_KEY on the server:**
```bash
openssl rand -hex 32
```

**Set proper permissions:**
```bash
sudo chmod 600 /var/www/ad-mint-ai/backend/.env
sudo chown www-data:www-data /var/www/ad-mint-ai/backend/.env
```

### 2.5 Restart Services

```bash
# Restart FastAPI service to load new environment variables
sudo systemctl restart fastapi

# Restart Nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status fastapi
sudo systemctl status nginx
```

### 2.6 Verify Backend Deployment

```bash
# Test health endpoint locally
curl http://127.0.0.1:8000/api/health

# Test through Nginx
curl http://YOUR_EC2_IP/api/health
```

Expected response:
```json
{"status":"healthy"}
```

---

## Step 3: Frontend Deployment

### 3.1 Build Frontend with Production API URL

**From your local machine** (not on EC2):

```bash
cd frontend

# Set production API URL
export VITE_API_URL=http://YOUR_EC2_IP

# Install dependencies (if not already done)
npm install

# Build for production
npm run build
```

### 3.2 Upload to S3

```bash
# Upload frontend to S3
aws s3 sync frontend/dist/ s3://ad-mint-ai-frontend/ --delete

# Verify upload
aws s3 ls s3://ad-mint-ai-frontend/
```

**Your frontend is now live at:**
`http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`

---

## Step 4: Verification & Testing

### 4.1 Test Backend Health

```bash
# From your local machine
curl http://YOUR_EC2_IP/api/health
```

### 4.2 Test Frontend

1. Open browser: `http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`
2. Check browser console for errors
3. Test API connectivity

### 4.3 Test Full Workflow

1. Register/Login via frontend
2. Create a video generation request
3. Verify video is uploaded to S3
4. Check video playback

### 4.4 Check Logs

**On EC2 instance:**
```bash
# FastAPI logs
sudo journalctl -u fastapi -f

# Nginx access logs
sudo tail -f /var/log/nginx/ad-mint-ai-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/ad-mint-ai-error.log
```

---

## Step 5: Service Management Commands

### FastAPI Service

```bash
# Check status
sudo systemctl status fastapi

# Start service
sudo systemctl start fastapi

# Stop service
sudo systemctl stop fastapi

# Restart service
sudo systemctl restart fastapi

# View logs
sudo journalctl -u fastapi -f
```

### Nginx Service

```bash
# Check status
sudo systemctl status nginx

# Reload configuration (no downtime)
sudo systemctl reload nginx

# Restart service
sudo systemctl restart nginx

# Test configuration
sudo nginx -t

# View logs
sudo tail -f /var/log/nginx/ad-mint-ai-error.log
```

---

## Step 6: Updating Application

### Update Backend

```bash
# SSH to EC2
ssh -i ad-mint-ai-key.pem ubuntu@YOUR_EC2_IP

# Pull latest code
cd /var/www/ad-mint-ai
git pull

# Update dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations (if any)
python -m app.db.init_db

# Restart service
sudo systemctl restart fastapi
```

### Update Frontend

```bash
# From local machine
cd frontend

# Set production API URL
export VITE_API_URL=http://YOUR_EC2_IP

# Build
npm run build

# Upload to S3
aws s3 sync dist/ s3://ad-mint-ai-frontend/ --delete
```

---

## Troubleshooting

### Backend Not Starting

```bash
# Check service logs
sudo journalctl -u fastapi -n 50 --no-pager

# Common issues:
# - Missing dependencies: Check import errors
# - Database connection: Verify DATABASE_URL in .env
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

### Frontend Not Connecting to Backend

1. Verify `VITE_API_URL` in frontend build matches your EC2 IP
2. Check browser console for CORS errors
3. Verify backend is accessible: `curl http://YOUR_EC2_IP/api/health`
4. Check security group allows HTTP (port 80)

### Database Connection Issues

```bash
# Test PostgreSQL connection (if using RDS)
psql -h RDS_ENDPOINT -U ad_mint_user -d ad_mint_ai

# Check security group rules
# Verify RDS is in same VPC as EC2
# Check security group allows port 5432 from EC2 SG
```

---

## Quick Reference

### Important URLs

- **Frontend**: `http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`
- **Backend API**: `http://YOUR_EC2_IP/api/`
- **Health Check**: `http://YOUR_EC2_IP/api/health`

### Key Files

- **Backend .env**: `/var/www/ad-mint-ai/backend/.env`
- **Nginx config**: `/etc/nginx/sites-available/ad-mint-ai`
- **Systemd service**: `/etc/systemd/system/fastapi.service`
- **Deployment path**: `/var/www/ad-mint-ai`

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | JWT secret key | Random 32+ character string |
| `STORAGE_MODE` | Storage backend | `s3` or `local` |
| `AWS_S3_VIDEO_BUCKET` | S3 bucket for videos | `ad-mint-ai-videos` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `REPLICATE_API_TOKEN` | Replicate API token | `r8_...` |

---

## Security Notes

⚠️ **Important Security Considerations**:

1. **No SSL/TLS**: Current deployment uses HTTP only
2. **CORS**: Configured to allow all origins
3. **Database**: RDS is in private subnet, not publicly accessible
4. **Credentials**: Store `.env` file securely, never commit to git
5. **SSH Access**: Consider restricting SSH (port 22) to your IP only

---

## Next Steps

- [ ] Configure domain name and DNS
- [ ] Set up SSL certificate (Let's Encrypt) for HTTPS
- [ ] Configure monitoring and alerting
- [ ] Set up automated backups
- [ ] Configure CI/CD pipeline for automated deployments

---

**Deployment Complete!** 🎉

Your application should now be accessible at:
- Frontend: `http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`
- Backend: `http://YOUR_EC2_IP/api/`

