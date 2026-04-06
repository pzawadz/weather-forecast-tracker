#!/bin/bash
#
# Deploy Weather Dashboard with CloudFront
# This script must be run by a user with AWS IAM permissions
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
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo "Instance: $INSTANCE_ID"
echo ""

# Step 1: Generate random secret
echo "📝 Generating CloudFront secret..."
SECRET_VALUE=$(openssl rand -hex 32)

# Step 2: Create secret in Secrets Manager
echo "🔐 Creating secret in AWS Secrets Manager..."
aws secretsmanager create-secret \
    --name weather-dashboard-cf-secret \
    --description "CloudFront validation secret for Weather Dashboard" \
    --secret-string "{\"secret\":\"$SECRET_VALUE\"}" \
    --region $REGION 2>&1 | grep ARN || echo "Secret already exists, updating..."

# If secret exists, update it
aws secretsmanager update-secret \
    --secret-id weather-dashboard-cf-secret \
    --secret-string "{\"secret\":\"$SECRET_VALUE\"}" \
    --region $REGION 2>&1 | grep ARN || true

echo "✅ Secret created/updated"
echo ""

# Step 3: Validate CloudFormation template
echo "🔍 Validating CloudFormation template..."
aws cloudformation validate-template \
    --template-body file://cloudformation-dashboard.yaml \
    --region $REGION > /dev/null

echo "✅ Template valid"
echo ""

# Step 4: Deploy CloudFormation stack
echo "🚀 Deploying CloudFormation stack..."
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
echo "✅ Stack deployed successfully!"
echo ""

# Step 5: Get outputs
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

# Get CloudFront URL
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
    --output text)

echo ""
echo "=================================="
echo "🎉 Deployment Complete!"
echo "=================================="
echo ""
echo "Dashboard URL: $CLOUDFRONT_URL"
echo ""
echo "⚠️  Note: CloudFront distribution may take 15-20 minutes to fully deploy."
echo "         Check status: aws cloudfront list-distributions --region us-east-1"
echo ""
echo "Next steps:"
echo "1. Wait for CloudFront to finish deploying"
echo "2. Access dashboard: $CLOUDFRONT_URL"
echo "3. Monitor logs: sudo journalctl -u weather-dashboard -f"
echo ""
