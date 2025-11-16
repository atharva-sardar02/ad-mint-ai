# Production Troubleshooting Guide

This guide covers common production issues and their solutions.

## Table of Contents

1. [Application Not Starting](#application-not-starting)
2. [Database Connection Issues](#database-connection-issues)
3. [S3 Storage Issues](#s3-storage-issues)
4. [Nginx Issues](#nginx-issues)
5. [Health Check Failures](#health-check-failures)
7. [Video Generation Failures](#video-generation-failures)
8. [Performance Issues](#performance-issues)

## Application Not Starting

### Symptoms
- FastAPI service status shows `failed` or `inactive`
- Health endpoint returns 503

### Diagnosis
```bash
# Check service status
sudo systemctl status fastapi

# Check logs
sudo journalctl -u fastapi -n 50 --no-pager

# Check for Python errors
cd /var/www/ad-mint-ai/backend
source venv/bin/activate
python -m app.main
```

### Common Causes and Solutions

**1. Environment variables not loaded**
- **Check**: Verify `.env` file exists at `/var/www/ad-mint-ai/backend/.env`
- **Fix**: Create `.env` file with required variables
- **Verify**: `sudo cat /var/www/ad-mint-ai/backend/.env` (check permissions)

**2. Database connection failed**
- **Check**: Verify `DATABASE_URL` in `.env` file
- **Fix**: Update `DATABASE_URL` with correct RDS endpoint and credentials
- **Test**: `psql $DATABASE_URL -c "SELECT 1;"`

**3. Missing dependencies**
- **Check**: `pip list` in virtual environment
- **Fix**: `pip install -r requirements.txt`

**4. Port already in use**
- **Check**: `sudo netstat -tulpn | grep 8000`
- **Fix**: Stop conflicting service or change port in systemd service file

## Database Connection Issues

### Symptoms
- Health endpoint shows database as unhealthy
- Application errors: "Connection refused" or "Authentication failed"

### Diagnosis
```bash
# Test connection from EC2
psql "postgresql://user:pass@rds-endpoint:5432/dbname"

# Check RDS security group
aws ec2 describe-security-groups --group-ids <rds-sg-id>

# Check RDS status
aws rds describe-db-instances --db-instance-identifier ad-mint-ai-db
```

### Common Causes and Solutions

**1. RDS security group not allowing EC2**
- **Check**: RDS security group inbound rules
- **Fix**: Add rule: Port 5432, Source: EC2 security group ID
- **Verify**: `aws ec2 describe-security-groups --group-ids <rds-sg-id>`

**2. Database connection string incorrect**
- **Check**: `DATABASE_URL` format is correct: `postgresql://user:pass@host:5432/dbname`
- **Fix**: Update `.env` file with correct connection string

**3. RDS instance not in same VPC**
- **Check**: RDS and EC2 are in same VPC
- **Fix**: Create RDS in same VPC as EC2, or configure VPC peering

**4. Database credentials incorrect**
- **Check**: Verify username/password in `.env` file
- **Fix**: Update credentials or reset RDS master password

## S3 Storage Issues

### Symptoms
- Video uploads fail
- Health endpoint shows S3 as unhealthy
- Errors: "Access Denied" or "Bucket not found"

### Diagnosis
```bash
# Test S3 connection
aws s3 ls s3://ad-mint-ai-videos/

# Check IAM permissions
aws iam get-role --role-name <ec2-iam-role-name>

# Test from application
curl http://localhost:8000/api/health
```

### Common Causes and Solutions

**1. IAM role not attached to EC2**
- **Check**: EC2 instance has IAM role with S3 permissions
- **Fix**: Attach IAM role to EC2 instance with `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` permissions

**2. AWS credentials not configured**
- **Check**: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env` file
- **Fix**: Add credentials to `.env` file or use IAM role (recommended)

**3. S3 bucket doesn't exist**
- **Check**: `aws s3 ls | grep ad-mint-ai-videos`
- **Fix**: Run `deployment/setup-s3-videos.sh` to create bucket

**4. Bucket policy too restrictive**
- **Check**: S3 bucket policy allows EC2 access
- **Fix**: Update bucket policy to allow IAM role or access key

## Nginx Issues

### Symptoms
- 502 Bad Gateway errors
- API requests not reaching FastAPI
- Nginx errors in logs

### Diagnosis
```bash
# Check Nginx status
sudo systemctl status nginx

# Check Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/ad-mint-ai-error.log
sudo tail -f /var/log/nginx/ad-mint-ai-access.log

# Test FastAPI directly
curl http://127.0.0.1:8000/api/health
```

### Common Causes and Solutions

**1. FastAPI not running**
- **Check**: `sudo systemctl status fastapi`
- **Fix**: `sudo systemctl start fastapi`

**2. Nginx configuration error**
- **Check**: `sudo nginx -t`
- **Fix**: Correct syntax errors in `/etc/nginx/sites-available/ad-mint-ai`

**3. Port 8000 not accessible**
- **Check**: FastAPI is listening on `127.0.0.1:8000`
- **Fix**: Verify `ExecStart` in systemd service file uses `--host 127.0.0.1 --port 8000`

**4. Proxy timeout**
- **Check**: Long-running requests timing out
- **Fix**: Increase `proxy_read_timeout` in Nginx config (default: 60s)

## Health Check Failures

### Symptoms
- Health endpoint returns 503
- Monitoring alerts triggered
- Component status shows "unhealthy"

### Diagnosis
```bash
# Check health endpoint
curl http://localhost:8000/api/health | jq

# Check individual components
# Database
psql $DATABASE_URL -c "SELECT 1;"

# S3
aws s3 ls s3://ad-mint-ai-videos/

# External APIs
echo $REPLICATE_API_TOKEN | cut -c1-10
echo $OPENAI_API_KEY | cut -c1-10
```

### Common Causes and Solutions

**1. Database connection failed**
- See [Database Connection Issues](#database-connection-issues)

**2. S3 connection failed**
- See [S3 Storage Issues](#s3-storage-issues)

**3. External API keys not configured**
- **Check**: `OPENAI_API_KEY` and `REPLICATE_API_TOKEN` in `.env`
- **Fix**: Add API keys to `.env` file

## Rate Limiting Issues

**Note**: Rate limiting has been removed per architecture. No rate limiting is configured.

## Video Generation Failures

### Symptoms
- Generation status stuck at "processing"
- Generation fails with error message
- No video file created

### Diagnosis
```bash
# Check generation logs
sudo journalctl -u fastapi -n 100 | grep "generation"

# Check S3 bucket
aws s3 ls s3://ad-mint-ai-videos/videos/

# Check Replicate API
curl -H "Authorization: Token $REPLICATE_API_TOKEN" https://api.replicate.com/v1/models
```

### Common Causes and Solutions

**1. Replicate API token invalid**
- **Check**: `REPLICATE_API_TOKEN` in `.env` file
- **Fix**: Update token or verify account status

**2. OpenAI API key invalid**
- **Check**: `OPENAI_API_KEY` in `.env` file
- **Fix**: Update API key or check account balance

**3. S3 upload failed**
- **Check**: S3 bucket permissions and connectivity
- **Fix**: See [S3 Storage Issues](#s3-storage-issues)

**4. Insufficient disk space**
- **Check**: `df -h` on EC2 instance
- **Fix**: Clean up temp files or increase disk size

## Performance Issues

### Symptoms
- Slow API responses
- High CPU/memory usage
- Timeout errors

### Diagnosis
```bash
# Check system resources
htop
df -h
free -h

# Check FastAPI logs for slow queries
sudo journalctl -u fastapi | grep "slow"

# Check database performance
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity;"
```

### Common Causes and Solutions

**1. Database connection pool exhausted**
- **Check**: Too many concurrent connections
- **Fix**: Adjust SQLAlchemy pool size in database configuration

**2. High memory usage**
- **Check**: Video processing uses significant memory
- **Fix**: Consider increasing EC2 instance size or optimizing video processing

**3. Slow S3 operations**
- **Check**: S3 upload/download times
- **Fix**: Use S3 transfer acceleration or optimize file sizes

## Emergency Procedures

### Restart All Services
```bash
sudo systemctl restart fastapi
sudo systemctl restart nginx
```

### Rollback to Previous Version
See `ROLLBACK.md` for detailed rollback procedures.

### Contact Information
- **On-Call Engineer**: [Your contact info]
- **AWS Support**: [Support plan details]
- **Emergency Escalation**: [Escalation path]

## Log File Locations

- **FastAPI Application**: `/var/log/fastapi/app.log`
- **Nginx Access**: `/var/log/nginx/ad-mint-ai-access.log`
- **Nginx Error**: `/var/log/nginx/ad-mint-ai-error.log`
- **Systemd Journal**: `sudo journalctl -u fastapi`

## Useful Commands

```bash
# View recent FastAPI logs
sudo journalctl -u fastapi -f

# Check service status
sudo systemctl status fastapi nginx

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Test database connection
psql $DATABASE_URL -c "SELECT version();"

# Test S3 access
aws s3 ls s3://ad-mint-ai-videos/
```

