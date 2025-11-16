#!/bin/bash
# Setup script for AWS RDS PostgreSQL instance
# This script provides instructions and validation for RDS setup
#
# Usage:
#   ./setup-rds.sh [region] [vpc-id]
#
# Arguments:
#   region: AWS region (default: us-east-1)
#   vpc-id: VPC ID where RDS should be created (required)
#
# Prerequisites:
#   - AWS CLI installed and configured
#   - Appropriate AWS credentials with RDS permissions
#   - VPC with public subnet (10.0.1.0/24) and private subnet (10.0.2.0/24)

set -e  # Exit on any error

# Configuration
REGION=${1:-us-east-1}
VPC_ID=${2:-""}
DB_INSTANCE_ID="ad-mint-ai-db"
DB_NAME="ad_mint_ai"
DB_USERNAME="ad_mint_user"
DB_PASSWORD=""  # Will be generated or prompted
DB_INSTANCE_CLASS="db.t3.micro"  # Adjust as needed
PRIVATE_SUBNET_GROUP="ad-mint-ai-private-subnet-group"
SECURITY_GROUP_NAME="ad-mint-ai-rds-sg"

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

echo "🚀 Setting up AWS RDS PostgreSQL instance"
echo "📍 Region: $REGION"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    error_exit "AWS CLI is not installed. Please install it first."
fi

# Check if VPC ID is provided
if [ -z "$VPC_ID" ]; then
    error_exit "VPC ID is required. Usage: ./setup-rds.sh [region] [vpc-id]"
fi

# Verify VPC exists
if ! aws ec2 describe-vpcs --vpc-ids "$VPC_ID" --region "$REGION" &> /dev/null; then
    error_exit "VPC $VPC_ID not found in region $REGION"
fi

info_msg "VPC verified: $VPC_ID"

# Find private subnet (10.0.2.0/24)
info_msg "Finding private subnet (10.0.2.0/24)..."
PRIVATE_SUBNET=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=cidr-block,Values=10.0.2.0/24" \
    --region "$REGION" \
    --query 'Subnets[0].SubnetId' \
    --output text)

if [ -z "$PRIVATE_SUBNET" ] || [ "$PRIVATE_SUBNET" = "None" ]; then
    error_exit "Private subnet (10.0.2.0/24) not found in VPC $VPC_ID"
fi

info_msg "Found private subnet: $PRIVATE_SUBNET"

# Find another private subnet for multi-AZ (if available)
PRIVATE_SUBNET_2=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=cidr-block,Values=10.0.2.0/24" \
    --region "$REGION" \
    --query 'Subnets[1].SubnetId' \
    --output text 2>/dev/null || echo "")

# Create DB subnet group
info_msg "Creating DB subnet group..."
if aws rds describe-db-subnet-groups --db-subnet-group-name "$PRIVATE_SUBNET_GROUP" --region "$REGION" &> /dev/null; then
    info_msg "DB subnet group already exists: $PRIVATE_SUBNET_GROUP"
else
    if [ -n "$PRIVATE_SUBNET_2" ] && [ "$PRIVATE_SUBNET_2" != "None" ]; then
        aws rds create-db-subnet-group \
            --db-subnet-group-name "$PRIVATE_SUBNET_GROUP" \
            --db-subnet-group-description "Private subnet group for Ad Mint AI RDS" \
            --subnet-ids "$PRIVATE_SUBNET" "$PRIVATE_SUBNET_2" \
            --region "$REGION" || error_exit "Failed to create DB subnet group"
    else
        aws rds create-db-subnet-group \
            --db-subnet-group-name "$PRIVATE_SUBNET_GROUP" \
            --db-subnet-group-description "Private subnet group for Ad Mint AI RDS" \
            --subnet-ids "$PRIVATE_SUBNET" \
            --region "$REGION" || error_exit "Failed to create DB subnet group"
    fi
    success_msg "DB subnet group created: $PRIVATE_SUBNET_GROUP"
fi

# Get EC2 security group ID (for RDS security group rule)
info_msg "Finding EC2 security group..."
EC2_SG=$(aws ec2 describe-security-groups \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=ad-mint-ai-ec2-sg" \
    --region "$REGION" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")

if [ -z "$EC2_SG" ] || [ "$EC2_SG" = "None" ]; then
    info_msg "EC2 security group not found. You'll need to create RDS security group manually."
    EC2_SG="<EC2_SECURITY_GROUP_ID>"
    info_msg "Note: You can find EC2 security group ID from EC2 instance details in AWS Console"
fi

# Create RDS security group
info_msg "Creating RDS security group..."
if aws ec2 describe-security-groups --group-names "$SECURITY_GROUP_NAME" --region "$REGION" &> /dev/null; then
    info_msg "Security group already exists: $SECURITY_GROUP_NAME"
    RDS_SG_ID=$(aws ec2 describe-security-groups \
        --group-names "$SECURITY_GROUP_NAME" \
        --region "$REGION" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)
else
    RDS_SG_ID=$(aws ec2 create-security-group \
        --group-name "$SECURITY_GROUP_NAME" \
        --description "Security group for Ad Mint AI RDS PostgreSQL" \
        --vpc-id "$VPC_ID" \
        --region "$REGION" \
        --query 'GroupId' \
        --output text)
    
    # Add inbound rule: PostgreSQL (5432) from EC2 security group only
    aws ec2 authorize-security-group-ingress \
        --group-id "$RDS_SG_ID" \
        --protocol tcp \
        --port 5432 \
        --source-group "$EC2_SG" \
        --region "$REGION" || info_msg "Note: EC2 security group rule may need manual configuration"
    
    success_msg "RDS security group created: $RDS_SG_ID"
fi

# Generate or prompt for database password
if [ -z "$DB_PASSWORD" ]; then
    info_msg "Generating secure database password..."
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    info_msg "Generated password (save this securely!): $DB_PASSWORD"
fi

# Check if DB instance already exists
if aws rds describe-db-instances --db-instance-identifier "$DB_INSTANCE_ID" --region "$REGION" &> /dev/null; then
    info_msg "RDS instance already exists: $DB_INSTANCE_ID"
    DB_ENDPOINT=$(aws rds describe-db-instances \
        --db-instance-identifier "$DB_INSTANCE_ID" \
        --region "$REGION" \
        --query 'DBInstances[0].Endpoint.Address' \
        --output text)
    success_msg "RDS endpoint: $DB_ENDPOINT"
else
    info_msg "Creating RDS PostgreSQL instance (this may take 10-15 minutes)..."
    
    aws rds create-db-instance \
        --db-instance-identifier "$DB_INSTANCE_ID" \
        --db-instance-class "$DB_INSTANCE_CLASS" \
        --engine postgres \
        --engine-version 15.4 \
        --master-username "$DB_USERNAME" \
        --master-user-password "$DB_PASSWORD" \
        --db-name "$DB_NAME" \
        --allocated-storage 20 \
        --storage-type gp3 \
        --db-subnet-group-name "$PRIVATE_SUBNET_GROUP" \
        --vpc-security-group-ids "$RDS_SG_ID" \
        --backup-retention-period 7 \
        --enable-automated-backups \
        --no-publicly-accessible \
        --region "$REGION" || error_exit "Failed to create RDS instance"
    
    info_msg "RDS instance creation initiated. Waiting for instance to be available..."
    aws rds wait db-instance-available \
        --db-instance-identifier "$DB_INSTANCE_ID" \
        --region "$REGION" || error_exit "RDS instance creation failed or timed out"
    
    DB_ENDPOINT=$(aws rds describe-db-instances \
        --db-instance-identifier "$DB_INSTANCE_ID" \
        --region "$REGION" \
        --query 'DBInstances[0].Endpoint.Address' \
        --output text)
    
    success_msg "RDS instance created successfully!"
fi

echo ""
success_msg "RDS PostgreSQL setup completed!"
echo ""
info_msg "Database Information:"
echo "  - Instance ID: $DB_INSTANCE_ID"
echo "  - Endpoint: $DB_ENDPOINT"
echo "  - Port: 5432"
echo "  - Database Name: $DB_NAME"
echo "  - Username: $DB_USERNAME"
echo "  - Password: $DB_PASSWORD"
echo "  - Backup Retention: 7 days (automated)"
echo "  - Publicly Accessible: No (private subnet only)"
echo ""
info_msg "Connection String (for .env file):"
echo "  DATABASE_URL=postgresql://$DB_USERNAME:$DB_PASSWORD@$DB_ENDPOINT:5432/$DB_NAME"
echo ""
info_msg "Next steps:"
echo "  1. Update backend .env file with DATABASE_URL"
echo "  2. Test database connection from EC2 instance"
echo "  3. Run database migrations: python -m app.db.init_db"
echo "  4. Verify automated backups are enabled (check AWS Console)"

