#!/bin/bash
# Setup script for S3 video storage bucket
# This script creates and configures the S3 bucket for video file storage
#
# Usage:
#   ./setup-s3-videos.sh [region]
#
# Arguments:
#   region: AWS region (default: us-east-1)
#
# Prerequisites:
#   - AWS CLI installed and configured
#   - Appropriate AWS credentials with S3 permissions

set -e  # Exit on any error

# Configuration
BUCKET_NAME="ad-mint-ai-videos"
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

echo "🚀 Setting up S3 video storage bucket: $BUCKET_NAME"
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

# Enable versioning (for backup/recovery)
info_msg "Enabling versioning..."
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled || error_exit "Failed to enable versioning"

success_msg "Versioning enabled"

# Set up lifecycle policy for cost optimization (transition to cheaper storage after 30 days)
info_msg "Setting up lifecycle policy..."
cat > /tmp/lifecycle-policy.json <<EOF
{
  "Rules": [
    {
      "Id": "TransitionToStandardIA",
      "Status": "Enabled",
      "Prefix": "",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        }
      ]
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
    --bucket "$BUCKET_NAME" \
    --lifecycle-configuration file:///tmp/lifecycle-policy.json || error_exit "Failed to set lifecycle policy"
rm /tmp/lifecycle-policy.json

success_msg "Lifecycle policy configured (transition to Standard-IA after 30 days)"

# Block public access (videos should not be publicly accessible)
info_msg "Blocking public access..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" || error_exit "Failed to block public access"

success_msg "Public access blocked"

# Configure CORS if needed for direct browser access (optional)
info_msg "Configuring CORS..."
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

success_msg "CORS configured"

echo ""
success_msg "S3 video storage bucket setup completed!"
echo ""
info_msg "Bucket Information:"
echo "  - Bucket Name: $BUCKET_NAME"
echo "  - Region: $REGION"
echo "  - Versioning: Enabled"
echo "  - Lifecycle Policy: Transition to Standard-IA after 30 days"
echo "  - Public Access: Blocked"
echo ""
info_msg "Next steps:"
echo "  1. Configure IAM role for EC2 instance with S3 access permissions"
echo "  2. Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in backend .env file"
echo "  3. Set STORAGE_MODE=s3 in backend .env file"
echo "  4. Set AWS_S3_VIDEO_BUCKET=$BUCKET_NAME in backend .env file"

