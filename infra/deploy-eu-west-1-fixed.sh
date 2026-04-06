#!/bin/bash
#
# Deploy Weather Dashboard - EU-WEST-1 (Fixed: all 3 AZs + port 8502)
#

set -e

STACK_NAME="weather-dashboard-eu"
REGION="eu-west-1"
INSTANCE_ID="i-0acff8ad77effe38c"
VPC_ID="vpc-01cfa6fef167dc90c"

echo "=================================="
echo "Weather Dashboard Deployment (FIXED)"
echo "Region: EU-WEST-1 (Ireland)"
echo "=================================="
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured."
    exit 1
fi

echo "✅ AWS Identity verified"
echo ""

# Get ALL subnets from VPC (need eu-west-1c!)
echo "🔍 Finding ALL subnets in VPC $VPC_ID..."
SUBNETS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[*].[SubnetId,AvailabilityZone]' \
    --output text \
    --region $REGION)

if [ -z "$SUBNETS" ]; then
    echo "❌ No subnets found"
    exit 1
fi

echo "Available subnets:"
echo "$SUBNETS"
echo ""

# Get subnet in eu-west-1c (where EC2 is) + one more
SUBNET_C=$(echo "$SUBNETS" | grep "eu-west-1c" | head -1 | awk '{print $1}')
SUBNET_OTHER=$(echo "$SUBNETS" | grep -v "eu-west-1c" | head -1 | awk '{print $1}')

if [ -z "$SUBNET_C" ]; then
    echo "❌ No subnet found in eu-west-1c"
    exit 1
fi

SUBNET_IDS="$SUBNET_C,$SUBNET_OTHER"

echo "✅ Using subnets: $SUBNET_IDS"
echo "   (includes eu-west-1c where EC2 is located)"
echo ""

# Download template
echo "📥 Downloading CloudFormation template..."
curl -sO https://raw.githubusercontent.com/pzawadz/weather-forecast-tracker/main/infra/cloudformation-dashboard-eu.yaml

if [ ! -f cloudformation-dashboard-eu.yaml ]; then
    echo "❌ Template download failed"
    exit 1
fi

echo "✅ Template downloaded"
echo ""

# Generate secret
echo "📝 Generating CloudFront secret..."
SECRET_VALUE=$(openssl rand -hex 32)

echo "🔐 Creating/updating secret..."
aws secretsmanager create-secret \
    --name weather-dashboard-cf-secret-eu \
    --description "CloudFront validation secret" \
    --secret-string "{\"secret\":\"$SECRET_VALUE\"}" \
    --region $REGION 2>&1 | grep ARN || {
        aws secretsmanager update-secret \
            --secret-id weather-dashboard-cf-secret-eu \
            --secret-string "{\"secret\":\"$SECRET_VALUE\"}" \
            --region $REGION 2>&1 | grep ARN || true
    }

echo "✅ Secret ready"
echo ""

# Deploy
echo "🚀 Deploying CloudFormation stack..."
echo "   Stack: $STACK_NAME"
echo "   VPC: $VPC_ID"
echo "   Subnets: $SUBNET_IDS"
echo "   Instance: $INSTANCE_ID"
echo "   Port: 8502 (FIXED!)"
echo ""

aws cloudformation deploy \
    --template-file cloudformation-dashboard-eu.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        InstanceId=$INSTANCE_ID \
        VpcId=$VPC_ID \
        SubnetIds=$SUBNET_IDS \
        DashboardPort=8502 \
    --capabilities CAPABILITY_IAM \
    --region $REGION

echo ""
echo "✅ Stack deployed!"
echo ""

# Get outputs
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

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
echo "Adding Security Group rule..."
aws ec2 authorize-security-group-ingress \
    --group-id $EC2_SG_ID \
    --protocol tcp \
    --port 8502 \
    --source-group $ALB_SG_ID \
    --region $REGION 2>&1 | grep -v "already exists" || echo "✅ Rule added (or already exists)"

echo ""
echo "⏳ Wait 2-3 minutes for:"
echo "   1. Target to become healthy"
echo "   2. CloudFront to propagate"
echo ""
echo "Then access: $CLOUDFRONT_URL"
echo ""
