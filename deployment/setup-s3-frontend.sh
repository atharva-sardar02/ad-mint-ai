#!/bin/bash
# Setup script for S3 frontend bucket
# This script creates and configures the S3 bucket for frontend static website hosting
#
# Usage:
#   ./setup-s3-frontend.sh [region]
#
# Arguments:
#   region: AWS region (default: us-east-1)
#
# Prerequisites:
#   - AWS CLI installed and configured
#   - Appropriate AWS credentials with S3 permissions

set -e  # Exit on any error

# Configuration
BUCKET_NAME="ad-mint-ai-frontend"
REGION=${1:-us-east-1}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error handling function
error_exit() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

# Success message function
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Info message function
info_msg() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

echo "🚀 Setting up S3 frontend bucket: $BUCKET_NAME"
echo "📍 Region: $REGION"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    error_exit "AWS CLI is not installed. Please install it first."
fi

# Check if bucket already exists
if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    info_msg "Bucket does not exist, creating..."
    
    # Create bucket
    if [ "$REGION" = "us-east-1" ]; then
        # us-east-1 doesn't require LocationConstraint
        aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" || error_exit "Failed to create bucket"
    else
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION" || error_exit "Failed to create bucket"
    fi
    
    success_msg "Bucket created: $BUCKET_NAME"
else
    info_msg "Bucket already exists: $BUCKET_NAME"
fi

# Enable static website hosting
info_msg "Enabling static website hosting..."
aws s3 website "s3://$BUCKET_NAME" \
    --index-document index.html \
    --error-document index.html || error_exit "Failed to enable static website hosting"

success_msg "Static website hosting enabled"

# Set bucket policy for public read access
info_msg "Setting bucket policy for public read access..."
cat > /tmp/bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file:///tmp/bucket-policy.json || error_exit "Failed to set bucket policy"
rm /tmp/bucket-policy.json

success_msg "Bucket policy set for public read access"

# Block public access settings (allow public read via policy)
info_msg "Configuring public access block settings..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" || error_exit "Failed to configure public access block"

success_msg "Public access block configured"

# Get website endpoint
WEBSITE_ENDPOINT=$(aws s3api get-bucket-website --bucket "$BUCKET_NAME" --query 'WebsiteConfiguration' --output json 2>/dev/null || echo "")
if [ -z "$WEBSITE_ENDPOINT" ]; then
    # Fallback: construct endpoint manually
    WEBSITE_ENDPOINT="http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
fi

echo ""
success_msg "S3 frontend bucket setup completed!"
echo ""
info_msg "Bucket Information:"
echo "  - Bucket Name: $BUCKET_NAME"
echo "  - Region: $REGION"
echo "  - Website Endpoint: $WEBSITE_ENDPOINT"
echo ""
# Configure CORS to allow all origins
info_msg "Configuring CORS (allows all origins)..."
cat > /tmp/cors-config.json <<EOF
{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": [],
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF

aws s3api put-bucket-cors \
    --bucket "$BUCKET_NAME" \
    --cors-configuration file:///tmp/cors-config.json || error_exit "Failed to configure CORS"
rm /tmp/cors-config.json

success_msg "CORS configured (allows all origins)"

echo ""
info_msg "Next steps:"
echo "  1. Build frontend: cd frontend && npm run build"
echo "  2. Upload to S3: aws s3 sync frontend/dist/ s3://$BUCKET_NAME/ --delete"
echo "  3. Set up DNS CNAME record pointing to: $WEBSITE_ENDPOINT"

