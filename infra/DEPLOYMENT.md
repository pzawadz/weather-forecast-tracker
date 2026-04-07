# Weather Dashboard - CloudFormation Deployment

## Architecture

```
Internet → CloudFront (HTTPS) → ALB (HTTP:80) → EC2:8502 (Streamlit)
```

**Security:**
- CloudFront adds secret header `X-CloudFront-Secret`
- ALB validates header (403 for direct access)
- Secret stored in AWS Secrets Manager
- EC2 Security Group allows traffic only from ALB

---

## Prerequisites

1. **EC2 Instance** running Streamlit dashboard on port 8502
2. **Systemd service** configured (see `weather-dashboard.service`)
3. **AWS CLI** configured with proper permissions
4. **VPC** with at least 2 subnets in different AZs

---

## Critical Configuration

### ⚠️ EC2 Instance Must Listen on 0.0.0.0

**Wrong:**
```bash
streamlit run dashboard.py --server.address=127.0.0.1  # ❌ ALB cannot reach
```

**Correct:**
```bash
streamlit run dashboard.py --server.address=0.0.0.0    # ✅ ALB can reach
```

**Verify:**
```bash
sudo ss -tlnp | grep 8502
# Should show: 0.0.0.0:8502 (not 127.0.0.1:8502)
```

### Health Check Endpoint

Target Group uses: `/_stcore/health`

This is Streamlit's native health check endpoint (returns `ok`).

**Test locally:**
```bash
curl http://localhost:8502/_stcore/health
# Should return: ok
```

---

## Deployment

### Option 1: Automated Script (Recommended)

```bash
# Download script
curl -O https://raw.githubusercontent.com/pzawadz/weather-forecast-tracker/main/infra/deploy-eu-west-1-fixed.sh
chmod +x deploy-eu-west-1-fixed.sh

# Run
./deploy-eu-west-1-fixed.sh
```

Script automatically:
1. Finds subnets in VPC (including eu-west-1c)
2. Creates/updates secret in Secrets Manager
3. Deploys CloudFormation stack
4. Adds Security Group rule (EC2:8502 ← ALB)
5. Displays CloudFront URL

---

### Option 2: Manual Deployment

#### Step 1: Create Secret

```bash
SECRET=$(openssl rand -hex 32)

aws secretsmanager create-secret \
    --name weather-dashboard-cf-secret-eu \
    --secret-string "{\"secret\":\"$SECRET\"}" \
    --region eu-west-1
```

#### Step 2: Get Subnet IDs

```bash
aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=vpc-01cfa6fef167dc90c" \
    --region eu-west-1 \
    --query 'Subnets[*].[SubnetId,AvailabilityZone]' \
    --output table
```

**Important:** Include subnet in **eu-west-1c** (where EC2 is located).

#### Step 3: Deploy Stack

```bash
aws cloudformation deploy \
    --template-file cloudformation-dashboard-eu.yaml \
    --stack-name weather-dashboard-eu \
    --parameter-overrides \
        InstanceId=i-0acff8ad77effe38c \
        VpcId=vpc-01cfa6fef167dc90c \
        SubnetIds=subnet-074feb79dcfd7b7f1,subnet-xxxxxx \
        DashboardPort=8502 \
    --capabilities CAPABILITY_IAM \
    --region eu-west-1
```

#### Step 4: Add Security Group Rule

```bash
# Get IDs from CloudFormation outputs
ALB_SG=$(aws cloudformation describe-stacks \
    --stack-name weather-dashboard-eu \
    --region eu-west-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBSecurityGroupId`].OutputValue' \
    --output text)

EC2_SG=$(aws ec2 describe-instances \
    --instance-ids i-0acff8ad77effe38c \
    --region eu-west-1 \
    --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
    --output text)

# Add rule
aws ec2 authorize-security-group-ingress \
    --group-id $EC2_SG \
    --protocol tcp \
    --port 8502 \
    --source-group $ALB_SG \
    --region eu-west-1
```

---

## Verification

### 1. Check Target Health

```bash
aws elbv2 describe-target-health \
    --target-group-arn $(aws elbv2 describe-target-groups \
        --names weather-dashboard-tg \
        --region eu-west-1 \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text) \
    --region eu-west-1
```

**Expected:** `"State": "healthy"`

### 2. Get CloudFront URL

```bash
aws cloudformation describe-stacks \
    --stack-name weather-dashboard-eu \
    --region eu-west-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
    --output text
```

### 3. Test Dashboard

```bash
curl -I https://YOUR_CLOUDFRONT_URL.cloudfront.net
# Should return: HTTP/2 200
```

Open in browser - dashboard should load.

---

## Troubleshooting

### Target is "unhealthy"

**Check 1: EC2 listening on 0.0.0.0?**
```bash
ssh ubuntu@172.31.13.147 "sudo ss -tlnp | grep 8502"
# Must show: 0.0.0.0:8502
```

**Fix:**
```bash
ssh ubuntu@172.31.13.147
sudo sed -i 's/--server.address=127.0.0.1/--server.address=0.0.0.0/g' \
    /etc/systemd/system/weather-dashboard.service
sudo systemctl daemon-reload
sudo systemctl restart weather-dashboard
```

**Check 2: Security Group allows ALB?**
```bash
aws ec2 describe-security-group-rules \
    --filters "Name=group-id,Values=$EC2_SG" \
    --region eu-west-1 \
    --query "SecurityGroupRules[?FromPort==\`8502\`]"
```

Should show rule allowing ALB Security Group.

**Check 3: Health check endpoint works?**
```bash
ssh ubuntu@172.31.13.147 "curl -s http://localhost:8502/_stcore/health"
# Should return: ok
```

---

### CloudFront returns 503

**Causes:**
1. Target is unhealthy (see above)
2. CloudFront still propagating (wait 15-20 minutes)
3. Wrong secret header (recreate secret in Secrets Manager)

**Check ALB directly:**
```bash
ALB_DNS=$(aws cloudformation describe-stacks \
    --stack-name weather-dashboard-eu \
    --region eu-west-1 \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBDNSName`].OutputValue' \
    --output text)

# This should fail (403 - no secret header)
curl -I http://$ALB_DNS

# This should work (200 - with secret header)
SECRET=$(aws secretsmanager get-secret-value \
    --secret-id weather-dashboard-cf-secret-eu \
    --region eu-west-1 \
    --query 'SecretString' \
    --output text | jq -r .secret)

curl -I -H "X-CloudFront-Secret: $SECRET" http://$ALB_DNS
```

---

### AZ Mismatch Error

**Error:** `Target is in an Availability Zone that is not enabled for the load balancer`

**Cause:** EC2 is in eu-west-1c, but ALB subnets only include eu-west-1a and eu-west-1b.

**Fix:** Use `deploy-eu-west-1-fixed.sh` - it automatically includes eu-west-1c subnet.

**Manual fix:**
```bash
# Find EC2 subnet
aws ec2 describe-instances \
    --instance-ids i-0acff8ad77effe38c \
    --region eu-west-1 \
    --query 'Reservations[0].Instances[0].[Placement.AvailabilityZone,SubnetId]'

# Update stack with correct subnets (must include eu-west-1c)
aws cloudformation update-stack \
    --stack-name weather-dashboard-eu \
    --use-previous-template \
    --parameters \
        ParameterKey=SubnetIds,ParameterValue="subnet-074feb79dcfd7b7f1,subnet-xxxxxx" \
    --region eu-west-1
```

---

## Stack Outputs

| Output | Description | Usage |
|--------|-------------|-------|
| `CloudFrontURL` | Public HTTPS URL | Share this URL |
| `ALBDNSName` | ALB internal DNS | Debugging |
| `ALBSecurityGroupId` | ALB Security Group | Add to EC2 rules |
| `TargetGroupArn` | Target Group ARN | Health check queries |

---

## Cost Estimate

| Service | Monthly Cost |
|---------|--------------|
| CloudFront | $1-5 (low traffic) |
| Application Load Balancer | $16-20 |
| Secrets Manager | $0.40 |
| **Total** | **~$17-25/month** |

EC2 cost not included (shared with gym tracker).

---

## Cleanup

```bash
# Delete stack
aws cloudformation delete-stack \
    --stack-name weather-dashboard-eu \
    --region eu-west-1

# Wait for deletion
aws cloudformation wait stack-delete-complete \
    --stack-name weather-dashboard-eu \
    --region eu-west-1

# Delete secret
aws secretsmanager delete-secret \
    --secret-id weather-dashboard-cf-secret-eu \
    --force-delete-without-recovery \
    --region eu-west-1
```

---

## Production Checklist

- [ ] EC2 listens on `0.0.0.0:8502`
- [ ] Systemd service auto-starts on boot
- [ ] Security Group allows ALB → EC2:8502
- [ ] Health check returns 200 OK
- [ ] Target shows "healthy" in Target Group
- [ ] CloudFront URL loads dashboard
- [ ] Secret stored in Secrets Manager
- [ ] Stack deployed successfully

---

## Files

- `cloudformation-dashboard-eu.yaml` - CloudFormation template
- `deploy-eu-west-1-fixed.sh` - Automated deployment script
- `weather-dashboard.service` - Systemd service file (reference)
- `DEPLOYMENT.md` - This file

---

## Support

**Issues:**
- Target unhealthy → Check EC2 bind address (0.0.0.0)
- 503 error → Verify Security Group rules
- AZ mismatch → Use deploy-eu-west-1-fixed.sh

**GitHub:** https://github.com/pzawadz/weather-forecast-tracker
