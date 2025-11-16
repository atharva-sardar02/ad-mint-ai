# GitHub Actions CI/CD Setup

This directory contains GitHub Actions workflows for automated testing and deployment.

## Workflows

### `deploy.yml` - Production Deployment

Automatically deploys to production when code is pushed to the `main` branch.

**What it does:**
1. ✅ Runs backend and frontend tests
2. ✅ Builds the frontend production bundle
3. ✅ Deploys backend to EC2 via SSH
4. ✅ Deploys frontend to S3 (optional)
5. ✅ Sends deployment notifications (optional)

## Setup Instructions

### 1. Configure GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions, and add:

#### Required Secrets (Backend Deployment)

- `EC2_HOST` - Your EC2 instance IP or hostname (e.g., `ec2-xx-xx-xx-xx.compute-1.amazonaws.com`)
- `EC2_USER` - SSH username (usually `ubuntu` for Ubuntu instances)
- `EC2_SSH_KEY` - Your private SSH key for EC2 access (full key including `-----BEGIN RSA PRIVATE KEY-----`)
- `EC2_DEPLOYMENT_PATH` - Path where app is deployed (default: `/var/www/ad-mint-ai`)
- `EC2_SSH_PORT` - SSH port (default: `22`)

#### Optional Secrets (Frontend S3 Deployment)

- `AWS_ACCESS_KEY_ID` - AWS access key with S3 permissions
- `AWS_SECRET_ACCESS_KEY` - AWS secret access key
- `AWS_REGION` - AWS region (default: `us-east-1`)
- `S3_FRONTEND_BUCKET` - S3 bucket name for frontend (e.g., `ad-mint-ai-frontend`)
- `CLOUDFRONT_DISTRIBUTION_ID` - CloudFront distribution ID (if using CDN)

#### Optional Secrets (Notifications & Configuration)

- `SLACK_WEBHOOK_URL` - Slack webhook for deployment notifications
- `VITE_API_URL` - Frontend API URL (default: `https://api.yourdomain.com`)
- `EC2_API_URL` - Backend API URL (default: `https://api.yourdomain.com`)
- `S3_FRONTEND_URL` - Frontend URL (default: `https://yourdomain.com`)

### 2. Set Up EC2 SSH Access

**Option A: Use SSH Key Pair (Recommended)**

1. Generate an SSH key pair if you don't have one:
   ```bash
   ssh-keygen -t rsa -b 4096 -C "github-actions"
   ```

2. Copy the public key to your EC2 instance:
   ```bash
   ssh-copy-id -i ~/.ssh/github_actions.pub ubuntu@your-ec2-host
   ```

3. Copy the private key content to GitHub Secrets as `EC2_SSH_KEY`:
   ```bash
   cat ~/.ssh/github_actions
   ```

**Option B: Use Existing EC2 Key Pair**

1. Convert your `.pem` file to the format needed:
   ```bash
   cat your-key.pem
   ```

2. Copy the entire output (including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`) to GitHub Secrets as `EC2_SSH_KEY`

### 3. Configure EC2 Instance

Ensure your EC2 instance has:

1. **Git repository access:**
   ```bash
   # On EC2 instance
   cd /var/www/ad-mint-ai
   git remote set-url origin https://github.com/your-username/ad-mint-ai.git
   # Or use SSH if you prefer
   ```

2. **Deployment script permissions:**
   ```bash
   chmod +x deployment/deploy.sh
   ```

3. **Sudo access for deployment user:**
   The deployment script needs sudo to install packages and configure services. Ensure your SSH user has sudo privileges.

### 4. Test the Workflow

1. Push a commit to the `main` branch
2. Go to Actions tab in GitHub to see the workflow run
3. Check deployment logs for any issues

## Workflow Triggers

- **Automatic:** Pushes to `main` branch
- **Manual:** Go to Actions → Deploy to Production → Run workflow

## Troubleshooting

### SSH Connection Fails

- Verify `EC2_HOST`, `EC2_USER`, and `EC2_SSH_KEY` are correct
- Check EC2 Security Group allows SSH from GitHub Actions IPs
- Test SSH connection manually: `ssh -i key.pem user@host`

### Deployment Script Fails

- Check EC2 instance has required dependencies
- Verify deployment path exists and has correct permissions
- Review EC2 logs: `sudo journalctl -u fastapi -f`

### Frontend Build Fails

- Check `VITE_API_URL` is set correctly
- Verify Node.js version matches (18+)
- Check for TypeScript or build errors

### S3 Deployment Fails

- Verify AWS credentials have S3 write permissions
- Check bucket name and region are correct
- Ensure bucket policy allows uploads

## Security Best Practices

1. **Never commit secrets** - Always use GitHub Secrets
2. **Use least privilege** - Grant only necessary AWS permissions
3. **Rotate keys regularly** - Update SSH and AWS keys periodically
4. **Enable 2FA** - Protect your GitHub account
5. **Review workflow logs** - Monitor for unauthorized access

## Customization

### Add Staging Environment

Create `.github/workflows/deploy-staging.yml` with similar configuration but:
- Trigger on `develop` branch
- Use different EC2 instance or S3 bucket
- Use `staging` environment in GitHub

### Add Approval Gate

Add an approval step before production deployment:

```yaml
deploy-backend:
  environment:
    name: production
    url: ${{ secrets.EC2_API_URL }}
    # Requires manual approval
```

### Add More Tests

Add additional test steps:
- Security scanning (Snyk, OWASP)
- Dependency checks (npm audit, safety)
- E2E tests (Playwright, Cypress)

## Support

For issues or questions:
1. Check workflow logs in GitHub Actions
2. Review deployment script logs on EC2
3. Consult Story 1.5 documentation: `docs/sprint-artifacts/1-5-production-deployment.md`

