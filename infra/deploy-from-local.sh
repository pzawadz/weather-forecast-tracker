#!/bin/bash
#
# Deploy Weather Dashboard from Local Machine
# Run this on your laptop/workstation with AWS credentials
#

set -e

STACK_NAME="weather-dashboard"
REGION="us-east-1"
INSTANCE_ID="i-0b403a5684524a722"
VPC_ID="vpc-098732f5e0774d174"
SUBNET_IDS="subnet-0a96c087fb3f9e5b6,subnet-0e8dc12c8a0bb7ff4"

echo "=================================="
echo "Weather Dashboard Deployment"
echo "=================================="
echo ""
echo "⚠️  This script requires AWS credentials with CloudFormation permissions."
echo "    Run on your local machine, not on EC2 instance."
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured."
    echo "   Run: aws configure"
    exit 1
fi

echo "AWS Identity:"
aws sts get-caller-identity
echo ""

# Step 1: Download template from GitHub
echo "📥 Downloading CloudFormation template..."
curl -sO https://raw.githubusercontent.com/pzawadz/weather-forecast-tracker/main/infra/cloudformation-dashboard.yaml

echo "✅ Template downloaded"
echo ""

# Step 2: Generate and store secret
echo "📝 Generating CloudFront secret..."
SECRET_VALUE=$(openssl rand -hex 32)

echo "🔐 Creating secret in AWS Secrets Manager..."
aws secretsmanager create-secret \
    --name weather-dashboard-cf-secret \
    --description "CloudFront validation secret for Weather Dashboard" \
    --secret-string "{\"secret\":\"$SECRET_VALUE\"}" \
    --region $REGION 2>&1 | grep ARN || {
        echo "Secret already exists, updating..."
        aws secretsmanager update-secret \
            --secret-id weather-dashboard-cf-secret \
            --secret-string "{\"secret\":\"$SECRET_VALUE\"}" \
            --region $REGION 2>&1 | grep ARN || true
    }

echo "✅ Secret created/updated"
echo ""

# Step 3: Validate template
echo "🔍 Validating CloudFormation template..."
aws cloudformation validate-template \
    --template-body file://cloudformation-dashboard.yaml \
    --region $REGION > /dev/null

echo "✅ Template valid"
echo ""

# Step 4: Deploy stack
echo "🚀 Deploying CloudFormation stack..."
echo "   This may take 5-10 minutes..."
echo ""

aws cloudformation deploy \
    --template-file cloudformation-dashboard.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        InstanceId=$INSTANCE_ID \
        VpcId=$VPC_ID \
        SubnetIds=$SUBNET_IDS \
    --capabilities CAPABILITY_IAM \
    --region $REGION

echo ""
echo "✅ Stack deployed!"
echo ""

# Step 5: Get outputs
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

# Get specific values
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
    --output text)

ALB_SG_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBSecurityGroupId`].OutputValue' \
    --output text)

echo ""
echo "=================================="
echo "🎉 Deployment Complete!"
echo "=================================="
echo ""
echo "Dashboard URL: $CLOUDFRONT_URL"
echo ""
echo "⚠️  CloudFront distribution is deploying (15-20 minutes)."
echo ""
echo "Next steps:"
echo ""
echo "1. Update EC2 Security Group to allow ALB access:"
echo "   - Go to EC2 Console → Security Groups"
echo "   - Find security group for instance $INSTANCE_ID"
echo "   - Add inbound rule:"
echo "     * Type: Custom TCP"
echo "     * Port: 8501"
echo "     * Source: $ALB_SG_ID"
echo ""
echo "2. Wait for CloudFront to finish deploying:"
echo "   Check status in CloudFront console"
echo ""
echo "3. Access dashboard:"
echo "   $CLOUDFRONT_URL"
echo ""
echo "4. Monitor logs on EC2:"
echo "   ssh ubuntu@44.201.26.33"
echo "   sudo journalctl -u weather-dashboard -f"
echo ""
