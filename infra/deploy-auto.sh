#!/bin/bash
#
# Deploy Weather Dashboard - Interactive subnet selection
#

set -e

STACK_NAME="weather-dashboard"
REGION="us-east-1"
INSTANCE_ID="i-0b403a5684524a722"
VPC_ID="vpc-098732f5e0774d174"

echo "=================================="
echo "Weather Dashboard Deployment"
echo "=================================="
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured."
    echo "   Run: aws configure"
    exit 1
fi

echo "✅ AWS Identity verified"
echo ""

# Get subnets from VPC
echo "🔍 Finding subnets in VPC $VPC_ID..."
SUBNETS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[*].[SubnetId,AvailabilityZone]' \
    --output text \
    --region $REGION)

if [ -z "$SUBNETS" ]; then
    echo "❌ No subnets found in VPC $VPC_ID"
    exit 1
fi

echo "Available subnets:"
echo "$SUBNETS"
echo ""

# Get first 2 subnets
SUBNET_1=$(echo "$SUBNETS" | head -1 | awk '{print $1}')
SUBNET_2=$(echo "$SUBNETS" | sed -n '2p' | awk '{print $1}')

if [ -z "$SUBNET_1" ] || [ -z "$SUBNET_2" ]; then
    echo "❌ Need at least 2 subnets in VPC"
    exit 1
fi

SUBNET_IDS="$SUBNET_1,$SUBNET_2"

echo "✅ Using subnets: $SUBNET_IDS"
echo ""

# Download template from GitHub
echo "📥 Downloading CloudFormation template..."
curl -sO https://raw.githubusercontent.com/pzawadz/weather-forecast-tracker/main/infra/cloudformation-dashboard.yaml

echo "✅ Template downloaded"
echo ""

# Generate and store secret
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

# Validate template
echo "🔍 Validating CloudFormation template..."
aws cloudformation validate-template \
    --template-body file://cloudformation-dashboard.yaml \
    --region $REGION > /dev/null

echo "✅ Template valid"
echo ""

# Deploy stack
echo "🚀 Deploying CloudFormation stack..."
echo "   Stack: $STACK_NAME"
echo "   VPC: $VPC_ID"
echo "   Subnets: $SUBNET_IDS"
echo "   Instance: $INSTANCE_ID"
echo ""
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

# Get outputs
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

# Get EC2 security group
EC2_SG_ID=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
    --output text \
    --region $REGION)

echo ""
echo "=================================="
echo "🎉 Deployment Complete!"
echo "=================================="
echo ""
echo "Dashboard URL: $CLOUDFRONT_URL"
echo ""
echo "⚠️  CloudFront distribution is deploying (15-20 minutes)."
echo ""
echo "Next step: Update EC2 Security Group"
echo ""
echo "Run this command to allow ALB → EC2:8501:"
echo ""
echo "aws ec2 authorize-security-group-ingress \\"
echo "    --group-id $EC2_SG_ID \\"
echo "    --protocol tcp \\"
echo "    --port 8501 \\"
echo "    --source-group $ALB_SG_ID \\"
echo "    --region $REGION"
echo ""
echo "Or manually in AWS Console:"
echo "  1. EC2 → Security Groups → $EC2_SG_ID"
echo "  2. Add inbound rule: TCP 8501 from $ALB_SG_ID"
echo ""
