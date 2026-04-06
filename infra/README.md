# Weather Dashboard - CloudFormation Deployment

## Architecture

```
Internet
   ↓
CloudFront (HTTPS)
   ↓ (secret header: X-CloudFront-Secret)
Application Load Balancer (HTTP:80)
   ↓ (port 8501)
EC2 Instance (Streamlit Dashboard)
```

## Prerequisites

1. **AWS CLI** configured with credentials
2. **IAM permissions** for:
   - CloudFormation
   - EC2 (SecurityGroups)
   - ELB (LoadBalancer, TargetGroup)
   - CloudFront
   - SecretsManager

3. **EC2 Security Group** must allow inbound 8501 from ALB security group

## Deployment Options

### Option A: Automated (with IAM permissions)

```bash
cd /home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker/infra
chmod +x deploy.sh
./deploy.sh
```

This will:
1. Generate random secret
2. Store in AWS Secrets Manager
3. Deploy CloudFormation stack
4. Output CloudFront URL

### Option B: Manual (via AWS Console)

#### Step 1: Create Secret

```bash
# Generate random secret
SECRET=$(openssl rand -hex 32)
echo "Secret: $SECRET"

# Create in Secrets Manager
aws secretsmanager create-secret \
    --name weather-dashboard-cf-secret \
    --description "CloudFront validation secret" \
    --secret-string "{\"secret\":\"$SECRET\"}" \
    --region us-east-1
```

#### Step 2: Deploy CloudFormation

1. Go to AWS Console → **CloudFormation**
2. Create stack → Upload template
3. Upload: `cloudformation-dashboard.yaml`
4. Parameters:
   - Stack name: `weather-dashboard`
   - InstanceId: `i-0b403a5684524a722`
   - VpcId: `vpc-098732f5e0774d174`
   - SubnetIds: `subnet-0a96c087fb3f9e5b6,subnet-0e8dc12c8a0bb7ff4`
5. Create stack

#### Step 3: Update EC2 Security Group

After stack creation, get ALB Security Group ID from outputs, then:

```bash
# Get ALB SG ID from CloudFormation outputs
ALB_SG_ID=$(aws cloudformation describe-stacks \
    --stack-name weather-dashboard \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBSecurityGroupId`].OutputValue' \
    --output text)

# Add inbound rule to EC2 security group
EC2_SG_ID="sg-xxxxxxxx"  # Your EC2 security group

aws ec2 authorize-security-group-ingress \
    --group-id $EC2_SG_ID \
    --protocol tcp \
    --port 8501 \
    --source-group $ALB_SG_ID \
    --region us-east-1
```

Or via Console:
1. EC2 → Security Groups → Find EC2 instance SG
2. Edit inbound rules → Add rule
3. Type: Custom TCP, Port: 8501
4. Source: Custom, paste ALB Security Group ID
5. Save

## Outputs

After deployment, get CloudFront URL:

```bash
aws cloudformation describe-stacks \
    --stack-name weather-dashboard \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
    --output text
```

Example: `https://d1a2b3c4d5e6f7.cloudfront.net`

## Monitoring

```bash
# Dashboard logs
sudo journalctl -u weather-dashboard -f

# ALB health checks
aws elbv2 describe-target-health \
    --target-group-arn <TARGET_GROUP_ARN>

# CloudFront distribution status
aws cloudfront list-distributions \
    --query 'DistributionList.Items[?Comment==`Weather Dashboard`].[Id,Status,DomainName]' \
    --output table
```

## Troubleshooting

### Dashboard not loading

1. Check Streamlit service:
   ```bash
   sudo systemctl status weather-dashboard
   ```

2. Check ALB target health:
   ```bash
   aws elbv2 describe-target-health --target-group-arn <ARN>
   ```

3. Verify EC2 security group allows 8501 from ALB

### 403 Forbidden

- CloudFront secret header mismatch
- Check secret in Secrets Manager matches CloudFormation template

### 504 Gateway Timeout

- Streamlit not running on EC2
- Port 8501 blocked by security group

## Cleanup

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name weather-dashboard

# Delete secret
aws secretsmanager delete-secret \
    --secret-id weather-dashboard-cf-secret \
    --force-delete-without-recovery
```

## Cost Estimate

- **CloudFront**: $0.085/GB (first 10TB) + $0.01 per 10,000 HTTPS requests
- **ALB**: $0.0225/hour + $0.008 per LCU-hour (~$16-20/month)
- **Secrets Manager**: $0.40/month per secret

**Estimated total**: ~$20-25/month for moderate traffic

## Security

- ✅ HTTPS via CloudFront (free TLS certificate)
- ✅ ALB protected by secret header (only CloudFront can access)
- ✅ No public port 8501 on EC2
- ✅ Secret stored in AWS Secrets Manager
- ⚠️  For production: Add WAF, custom domain, ACM certificate

## Custom Domain (optional)

1. Get ACM certificate in **us-east-1** (required for CloudFront)
2. Update CloudFormation:
   - Add `Aliases` to CloudFront distribution
   - Add `ViewerCertificate` with ACM ARN
3. Update DNS: CNAME → CloudFront distribution domain

Example:
```yaml
Aliases:
  - weather.yourdomain.com
ViewerCertificate:
  AcmCertificateArn: arn:aws:acm:us-east-1:123456789012:certificate/xxx
  SslSupportMethod: sni-only
```
