# Fix Temp Folder Permissions and CORS

## Quick Fix Commands

```bash
# SSH into production
ssh -i ad-mint-ai-key.pem ubuntu@44.210.144.149

# Fix temp folder permissions
cd /var/www/ad-mint-ai/backend
sudo mkdir -p temp/master_mode
sudo chown -R www-data:www-data temp
sudo chmod -R 755 temp

# Also fix tmp folder (used by MoviePy)
sudo mkdir -p tmp
sudo chown -R www-data:www-data tmp
sudo chmod -R 755 tmp

# Fix output/temp folder (used by regular pipeline)
sudo mkdir -p output/temp
sudo chown -R www-data:www-data output
sudo chmod -R 755 output

# Restart FastAPI
sudo systemctl restart fastapi

# Check logs
sudo journalctl -u fastapi -n 50 --no-pager
```

## Fix CORS Issue

The frontend is on S3 at `http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com` but CORS might not be configured correctly.

```bash
# Check current CORS config
cat /var/www/ad-mint-ai/backend/.env | grep CORS

# Update .env file to include S3 frontend URL
sudo nano /var/www/ad-mint-ai/backend/.env
```

Add or update:
```bash
CORS_ALLOWED_ORIGINS=http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com,http://44.210.144.149
```

Then restart:
```bash
sudo systemctl restart fastapi
```

## Verify

```bash
# Test health endpoint
curl http://127.0.0.1:8000/api/health

# Check temp folder exists and has right permissions
ls -la /var/www/ad-mint-ai/backend/temp
ls -la /var/www/ad-mint-ai/backend/tmp
ls -la /var/www/ad-mint-ai/backend/output
```

