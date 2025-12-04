#!/bin/bash
# ============================================================================
# AWS Infrastructure Setup Script
# ============================================================================
# This script helps you set up the AWS infrastructure for TikTrend Finder
# Usage: ./setup.sh
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "============================================"
echo "  TikTrend Finder - AWS Infrastructure Setup"
echo "============================================"
echo -e "${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}✗ Terraform not found. Please install Terraform >= 1.5.0${NC}"
    echo "  https://developer.hashicorp.com/terraform/downloads"
    exit 1
fi
TERRAFORM_VERSION=$(terraform version -json | jq -r '.terraform_version')
echo -e "${GREEN}✓ Terraform $TERRAFORM_VERSION installed${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI not found. Please install AWS CLI${NC}"
    echo "  https://aws.amazon.com/cli/"
    exit 1
fi
AWS_VERSION=$(aws --version | cut -d/ -f2 | cut -d' ' -f1)
echo -e "${GREEN}✓ AWS CLI $AWS_VERSION installed${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}✗ AWS credentials not configured${NC}"
    echo "  Run: aws configure"
    exit 1
fi
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
echo -e "${GREEN}✓ AWS Account: $AWS_ACCOUNT_ID${NC}"
echo -e "${GREEN}✓ AWS Region: $AWS_REGION${NC}"

# Check if terraform.tfvars exists
echo ""
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${YELLOW}Creating terraform.tfvars from example...${NC}"
    cp production.tfvars.example terraform.tfvars
    echo -e "${RED}⚠️  Please edit terraform.tfvars with your values before continuing!${NC}"
    echo ""
    echo "Required changes:"
    echo "  - domain_name: Your registered domain"
    echo "  - db_password: Strong database password"
    echo "  - jwt_secret_key: Random 32+ character string"
    echo "  - openai_api_key: Your OpenAI API key"
    echo "  - mercadopago_access_token: Your MercadoPago credentials"
    echo ""
    read -p "Press Enter after editing terraform.tfvars to continue..."
fi

# Initialize Terraform
echo ""
echo -e "${YELLOW}Initializing Terraform...${NC}"
terraform init

# Validate configuration
echo ""
echo -e "${YELLOW}Validating Terraform configuration...${NC}"
terraform validate

# Format check
echo ""
echo -e "${YELLOW}Checking Terraform formatting...${NC}"
terraform fmt -check -recursive || {
    echo -e "${YELLOW}Fixing formatting...${NC}"
    terraform fmt -recursive
}

# Plan
echo ""
echo -e "${YELLOW}Creating execution plan...${NC}"
terraform plan -var-file="terraform.tfvars" -out=tfplan

# Ask for confirmation
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${YELLOW}Ready to deploy infrastructure${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "Resources that will be created:"
echo "  - VPC with 3 AZs"
echo "  - RDS PostgreSQL database"
echo "  - ElastiCache Redis cluster"
echo "  - ECS Fargate cluster"
echo "  - Application Load Balancer"
echo "  - CloudFront CDN"
echo "  - S3 buckets"
echo "  - Secrets Manager"
echo "  - CloudWatch monitoring"
echo ""
echo -e "${RED}⚠️  This will incur AWS charges (~$200-275/month)${NC}"
echo ""

read -p "Do you want to apply this plan? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Apply
echo ""
echo -e "${YELLOW}Applying Terraform plan...${NC}"
terraform apply tfplan

# Output important values
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Infrastructure deployed successfully! 🎉${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Important outputs:"
terraform output

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Configure your domain's nameservers to Route53"
echo "2. Set up GitHub Actions secrets (see README.md)"
echo "3. Push to main branch to trigger deployment"
echo ""
echo -e "${BLUE}Documentation: README.md${NC}"
