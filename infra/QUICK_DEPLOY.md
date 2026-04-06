# 🚀 Quick Deploy Guide - CloudFront Dashboard

## TL;DR (dla zaawansowanych)

```bash
# Na twoim komputerze (z AWS credentials)
curl -o deploy.sh https://raw.githubusercontent.com/pzawadz/weather-forecast-tracker/main/infra/deploy-from-local.sh
chmod +x deploy.sh
./deploy.sh

# Potem: dodaj inbound rule do EC2 SG (port 8501 from ALB SG)
# CloudFront URL pojawi się w output
```

---

## Krok po kroku

### Wymagania

1. **AWS CLI** zainstalowane
2. **AWS Credentials** skonfigurowane (`aws configure`)
3. **Uprawnienia IAM**:
   - CloudFormation: CreateStack, DescribeStacks
   - EC2: CreateSecurityGroup, AuthorizeSecurityGroupIngress
   - ElasticLoadBalancing: CreateLoadBalancer, CreateTargetGroup
   - CloudFront: CreateDistribution
   - SecretsManager: CreateSecret

### 1️⃣ Pobierz skrypt

```bash
cd ~/Downloads  # lub dowolny folder

curl -O https://raw.githubusercontent.com/pzawadz/weather-forecast-tracker/main/infra/deploy-from-local.sh
chmod +x deploy-from-local.sh
```

### 2️⃣ Uruchom deployment

```bash
./deploy-from-local.sh
```

Skrypt automatycznie:
- Pobiera CloudFormation template z GitHub
- Generuje losowy secret dla CloudFront
- Tworzy secret w AWS Secrets Manager
- Deploy'uje CloudFormation stack
- Wyświetla CloudFront URL

**Czas deploymentu:** 5-10 minut (stack) + 15-20 minut (CloudFront propagation)

### 3️⃣ Zaktualizuj EC2 Security Group

Po deployment, skrypt poda **ALB Security Group ID**. Musisz dodać regułę do EC2:

#### Opcja A: AWS Console

1. EC2 → **Security Groups**
2. Znajdź security group dla `i-0b403a5684524a722` (dev machine)
3. **Edit inbound rules** → **Add rule**
4. Konfiguracja:
   - Type: **Custom TCP**
   - Port: **8501**
   - Source: **Custom** → wklej ALB Security Group ID
   - Description: `ALB to Streamlit dashboard`
5. **Save rules**

#### Opcja B: AWS CLI

```bash
# Pobierz ALB SG ID z CloudFormation
ALB_SG_ID=$(aws cloudformation describe-stacks \
    --stack-name weather-dashboard \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBSecurityGroupId`].OutputValue' \
    --output text)

# Znajdź EC2 SG ID
EC2_SG_ID=$(aws ec2 describe-instances \
    --instance-ids i-0b403a5684524a722 \
    --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
    --output text)

# Dodaj regułę
aws ec2 authorize-security-group-ingress \
    --group-id $EC2_SG_ID \
    --protocol tcp \
    --port 8501 \
    --source-group $ALB_SG_ID \
    --region us-east-1
```

### 4️⃣ Czekaj na CloudFront

CloudFront distribution potrzebuje **15-20 minut** na propagację.

Sprawdź status:
```bash
aws cloudfront list-distributions \
    --query 'DistributionList.Items[?Comment==`Weather Dashboard`].[Id,Status,DomainName]' \
    --output table
```

Status: `InProgress` → `Deployed`

### 5️⃣ Testuj dashboard

```bash
# Pobierz URL
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name weather-dashboard \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
    --output text)

echo "Dashboard: $CLOUDFRONT_URL"

# Otwórz w przeglądarce
open "$CLOUDFRONT_URL"  # macOS
xdg-open "$CLOUDFRONT_URL"  # Linux
start "$CLOUDFRONT_URL"  # Windows Git Bash
```

---

## Troubleshooting

### ❌ 403 Forbidden

**Przyczyna:** Secret header mismatch

**Rozwiązanie:**
```bash
# Sprawdź secret
aws secretsmanager get-secret-value \
    --secret-id weather-dashboard-cf-secret \
    --query SecretString \
    --output text

# Jeśli nieprawidłowy, usuń stack i deploy ponownie
aws cloudformation delete-stack --stack-name weather-dashboard
# Poczekaj 5 minut
./deploy-from-local.sh
```

### ❌ 504 Gateway Timeout

**Przyczyna:** Streamlit nie działa lub EC2 SG blokuje port 8501

**Rozwiązanie:**
```bash
# Sprawdź na EC2
ssh ubuntu@44.201.26.33
sudo systemctl status weather-dashboard

# Jeśli nie działa
sudo systemctl restart weather-dashboard

# Sprawdź SG (powinien być rule dla 8501 from ALB SG)
```

### ❌ 502 Bad Gateway

**Przyczyna:** ALB nie może połączyć się z EC2:8501

**Rozwiązanie:**
1. Sprawdź EC2 Security Group (punkt 3️⃣ powyżej)
2. Sprawdź czy Streamlit działa: `sudo systemctl status weather-dashboard`

### ❌ "Secret already exists"

**To jest OK!** Skrypt automatycznie update'uje istniejący secret.

---

## Sprawdź czy działa

### Health Check

```bash
# ALB target health
aws elbv2 describe-target-health \
    --target-group-arn $(aws elbv2 describe-target-groups \
        --names weather-dashboard-tg \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
```

Oczekiwany status: `healthy`

### Test lokalny (na EC2)

```bash
ssh ubuntu@44.201.26.33
curl -s http://localhost:8501/_stcore/health
# Powinno zwrócić: ok
```

### CloudFront

```bash
# Status distribution
aws cloudfront list-distributions \
    --query 'DistributionList.Items[?Comment==`Weather Dashboard`].[Status,DomainName]' \
    --output table
```

---

## Cleanup (usunięcie)

```bash
# Usuń CloudFormation stack
aws cloudformation delete-stack --stack-name weather-dashboard

# Usuń secret
aws secretsmanager delete-secret \
    --secret-id weather-dashboard-cf-secret \
    --force-delete-without-recovery

# Usuń regułę z EC2 SG (opcjonalnie)
# Znajdź SG rule ID i usuń przez console lub CLI
```

---

## Koszty

- **CloudFront**: ~$1-5/miesiąc (niski traffic)
- **ALB**: ~$16-20/miesiąc
- **Secrets Manager**: $0.40/miesiąc

**Total**: ~$17-25/miesiąc

---

## Co dalej?

### Własna domena (opcjonalnie)

1. **Certyfikat ACM** (us-east-1):
   ```bash
   aws acm request-certificate \
       --domain-name weather.yourdomain.com \
       --validation-method DNS \
       --region us-east-1
   ```

2. **Zweryfikuj** przez DNS (dodaj CNAME record)

3. **Update CloudFormation template**:
   ```yaml
   Aliases:
     - weather.yourdomain.com
   ViewerCertificate:
     AcmCertificateArn: arn:aws:acm:us-east-1:123:certificate/xxx
     SslSupportMethod: sni-only
   ```

4. **DNS CNAME**:
   ```
   weather.yourdomain.com → d1a2b3c4d5e6f7.cloudfront.net
   ```

### Monitoring

- **CloudWatch Logs** dla ALB
- **CloudFront Metrics** w CloudWatch
- **X-Ray** dla request tracing (advanced)

---

**Potrzebujesz pomocy?** Zobacz pełną dokumentację: `infra/README.md`
