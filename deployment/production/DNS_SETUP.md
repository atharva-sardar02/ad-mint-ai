# Domain and DNS Configuration Guide

This guide covers domain name and DNS configuration for production deployment.

## Overview

- **Frontend**: Hosted on S3 static website hosting
- **Backend API**: Hosted on EC2 instance
- **DNS Records**: CNAME for frontend, A record for API

## Prerequisites

- Domain name registered
- Access to domain DNS management (Route 53, Cloudflare, etc.)
- S3 bucket `ad-mint-ai-frontend` created and configured
- EC2 instance with static public IP (or Elastic IP)

## Step 1: Get S3 Website Endpoint

```bash
# Get S3 website endpoint
aws s3api get-bucket-website \
    --bucket ad-mint-ai-frontend \
    --region us-east-1

# Or construct manually:
# Format: http://ad-mint-ai-frontend.s3-website-<region>.amazonaws.com
# Example: http://ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com
```

**Note**: Save this endpoint URL for DNS configuration.

## Step 2: Get EC2 Public IP

```bash
# Get EC2 instance public IP
aws ec2 describe-instances \
    --instance-ids <instance-id> \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text

# Or use Elastic IP (recommended for production)
aws ec2 describe-addresses \
    --filters "Name=instance-id,Values=<instance-id>"
```

**Note**: For production, use Elastic IP to avoid IP changes on instance restart.

## Step 3: Configure DNS Records

### Option A: Using AWS Route 53

```bash
# Create hosted zone (if not exists)
aws route53 create-hosted-zone \
    --name yourdomain.com \
    --caller-reference $(date +%s)

# Get hosted zone ID
ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --dns-name yourdomain.com \
    --query 'HostedZones[0].Id' \
    --output text | cut -d'/' -f3)

# Create CNAME record for frontend (www subdomain)
aws route53 change-resource-record-sets \
    --hosted-zone-id $ZONE_ID \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "www.yourdomain.com",
                "Type": "CNAME",
                "TTL": 300,
                "ResourceRecords": [{
                    "Value": "ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com"
                }]
            }
        }]
    }'

# Create A record for API (api subdomain)
aws route53 change-resource-record-sets \
    --hosted-zone-id $ZONE_ID \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "api.yourdomain.com",
                "Type": "A",
                "TTL": 300,
                "ResourceRecords": [{
                    "Value": "<EC2_PUBLIC_IP>"
                }]
            }
        }]
    }'
```

### Option B: Using Cloudflare

1. Add domain to Cloudflare
2. Update nameservers at domain registrar
3. Create DNS records:
   - **Type**: CNAME
   - **Name**: www
   - **Target**: `ad-mint-ai-frontend.s3-website-us-east-1.amazonaws.com`
   - **Proxy**: Off (DNS only)
   
   - **Type**: A
   - **Name**: api
   - **IPv4 address**: `<EC2_PUBLIC_IP>`
   - **Proxy**: Off (DNS only)

### Option C: Using Other DNS Providers

**Frontend (CNAME)**:
- **Type**: CNAME
- **Name**: www (or @ for root domain)
- **Value**: `ad-mint-ai-frontend.s3-website-<region>.amazonaws.com`
- **TTL**: 300 (5 minutes)

**API (A Record)**:
- **Type**: A
- **Name**: api
- **Value**: `<EC2_PUBLIC_IP>`
- **TTL**: 300 (5 minutes)

## Step 4: Update S3 Bucket CORS

```bash
# Update S3 bucket CORS to allow API domain
cat > /tmp/cors-config.json <<EOF
{
  "CORSRules": [
    {
      "AllowedOrigins": [
        "https://www.yourdomain.com",
        "https://yourdomain.com"
      ],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": [],
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF

aws s3api put-bucket-cors \
    --bucket ad-mint-ai-frontend \
    --cors-configuration file:///tmp/cors-config.json
```

## Step 5: Update FastAPI CORS Configuration

Update `/var/www/ad-mint-ai/backend/.env`:

```bash
CORS_ALLOWED_ORIGINS=https://www.yourdomain.com,https://yourdomain.com
```

Restart FastAPI:
```bash
sudo systemctl restart fastapi
```

## Step 6: Update Nginx Configuration

Update `/etc/nginx/sites-available/ad-mint-ai`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;  # Update this line
    
    # ... rest of configuration
}
```

Test and reload Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Step 7: Verify DNS Resolution

```bash
# Check frontend DNS
dig www.yourdomain.com
nslookup www.yourdomain.com

# Check API DNS
dig api.yourdomain.com
nslookup api.yourdomain.com

# Test frontend access
curl -I https://www.yourdomain.com

# Test API access
curl https://api.yourdomain.com/api/health
```

## Step 8: SSL/TLS Configuration (Optional)

**Note**: Per architecture design, SSL/TLS is not required. The application uses HTTP only. If you want to add SSL/TLS later, options include:

### Option A: Cloudflare SSL (Easiest)

1. Enable Cloudflare proxy (Orange cloud)
2. SSL/TLS mode: Full (strict)
3. Automatic HTTPS redirect enabled

### Option B: AWS Certificate Manager + CloudFront

1. Request SSL certificate in ACM
2. Create CloudFront distribution for S3 bucket
3. Update DNS to point to CloudFront distribution
4. Configure SSL for EC2 using ALB or CloudFront

### Option C: Let's Encrypt on EC2

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal (already configured)
sudo certbot renew --dry-run
```

## Verification Checklist

- [ ] Frontend DNS resolves to S3 website endpoint
- [ ] API DNS resolves to EC2 public IP
- [ ] Frontend loads correctly from domain
- [ ] API health endpoint accessible from domain
- [ ] CORS allows requests from frontend domain
- [ ] SSL/TLS configured (optional - not required per architecture)
- [ ] Nginx `server_name` matches API domain
- [ ] FastAPI CORS configuration updated

## Troubleshooting

### DNS Not Resolving

**Check**:
- DNS propagation: `dig yourdomain.com`
- Nameserver configuration at registrar
- TTL values (lower TTL for faster updates)

**Fix**:
- Wait for DNS propagation (up to 48 hours, usually < 1 hour)
- Verify nameservers are correct
- Clear DNS cache: `sudo systemd-resolve --flush-caches`

### CORS Errors

**Check**:
- S3 bucket CORS configuration
- FastAPI CORS allowed origins
- Browser console for CORS errors

**Fix**:
- Update S3 CORS to include frontend domain
- Update FastAPI `.env` with correct origins
- Verify domain matches exactly (including https://)

### SSL Certificate Issues (If Using SSL)

**Note**: SSL/TLS is optional per architecture. If you choose to add SSL:

**Check**:
- Certificate validity: `openssl s_client -connect api.yourdomain.com:443`
- Certificate matches domain
- Nginx SSL configuration

**Fix**:
- Renew certificate if expired
- Verify domain ownership
- Check Nginx SSL configuration

## Maintenance

### Regular Tasks

- **Monthly**: Verify DNS records are correct
- **Quarterly**: Review SSL certificate expiration (if using SSL)
- **Annually**: Review domain registration

### Monitoring

- Monitor DNS resolution: `dig yourdomain.com`
- Monitor SSL certificate expiration (if using SSL)
- Monitor domain registration expiration

## Contact Information

- **DNS Provider**: [Provider name and support]
- **Domain Registrar**: [Registrar name and support]
- **AWS Support**: [Support plan details]

