# GitHub Actions CI/CD Setup

This directory contains GitHub Actions workflows for automated deployment.

## Workflows

### `deploy.yml` - Production Deployment

Automatically deploys both frontend and backend to production when code is pushed to the `main` branch.

**What it does:**
1. ✅ Builds frontend with production API URL
2. ✅ Deploys frontend to S3 bucket
3. ✅ Creates backup of current backend deployment
4. ✅ Deploys backend to EC2 via SSH
5. ✅ Performs health check (polls `/api/health` for 60 seconds)
6. ✅ Automatically rolls back if health check fails

**Key Features:**
- Zero-downtime deployment with health checks
- Automatic rollback on failure
- Backup preservation for manual recovery
- No tests (deploys directly as configured)

## Setup Instructions

### 1. Configure GitHub Secrets

Go to your repository → **Settings** → **Secrets and variables** → **Actions**, and add:

#### Required Secrets

| Secret Name | Description | Example |
|------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 deployment | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 deployment | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `EC2_USERNAME` | SSH username for EC2 instance | `ubuntu` |
| `EC2_SSH_KEY` | **Complete private key content** from `.pem` file | Copy entire contents of `ad-mint-ai-key.pem` |

**Important:**
- `EC2_SSH_KEY` should contain the **entire private key file content** (including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`)
- Open your `.pem` file and copy everything, then paste into the GitHub Secret

### 2. EC2 Instance Requirements

Your EC2 instance must have:

1. **Git repository cloned:**
   ```bash
   # On EC2 instance
   cd /var/www/ad-mint-ai
   git remote -v  # Should show your GitHub repo
   ```

2. **Git configured for pull:**
   ```bash
   # Ensure git can pull without credentials (or use SSH)
   git config --global credential.helper store
   ```

3. **Deployment directory permissions:**
   ```bash
   sudo chown -R ubuntu:ubuntu /var/www/ad-mint-ai
   ```

4. **FastAPI service running:**
   ```bash
   sudo systemctl status fastapi  # Should be active
   ```

### 3. Test the Workflow

1. Push a commit to the `main` branch
2. Go to **Actions** tab in GitHub to see the workflow run
3. Check deployment logs for any issues
4. Verify health endpoint: `http://44.210.144.149/api/health`

## Workflow Triggers

- **Automatic:** Pushes to `main` branch
- **Manual:** Go to **Actions** → **Deploy to Production** → **Run workflow**

## Deployment Process

### Frontend Deployment

1. Builds frontend with `VITE_API_URL=http://44.210.144.149`
2. Syncs `frontend/dist/` to S3 bucket `ad-mint-ai-frontend`
3. Verifies `index.html` exists in S3

### Backend Deployment

1. **Backup:** Creates `/var/www/ad-mint-ai.backup` directory
2. **Pull Code:** `git reset --hard origin/main`
3. **Update Dependencies:** `pip install -r requirements.txt`
4. **Run Migrations:** `python -m app.db.migrations.run_all` (runs all migrations automatically)
5. **Restart Service:** `sudo systemctl restart fastapi`
6. **Health Check:** Polls `/api/health` every 5 seconds for up to 60 seconds
7. **Rollback (if needed):** Restores from backup and restarts service

## Health Check

The workflow performs a health check after backend deployment:

- **Endpoint:** `http://44.210.144.149/api/health`
- **Expected Response:** `{"status": "healthy", ...}`
- **Polling:** Every 5 seconds for up to 60 seconds (12 attempts)
- **Failure:** Triggers automatic rollback

## Rollback

If health check fails:

1. **Automatic Rollback:**
   - Stops FastAPI service
   - Restores `/var/www/ad-mint-ai` from backup
   - Preserves `.env` file
   - Restarts service
   - Fails workflow with error message

2. **Manual Rollback:**
   ```bash
   ssh -i ad-mint-ai-key.pem ubuntu@44.210.144.149
   cd /var/www/ad-mint-ai.backup
   # Use deployment/scripts/rollback.sh
   ```

## Troubleshooting

### SSH Connection Fails

- Verify `EC2_USERNAME` and `EC2_SSH_KEY` are correct
- Check EC2 Security Group allows SSH (port 22) from GitHub Actions IPs
- Test SSH connection manually: `ssh -i key.pem ubuntu@44.210.144.149`

### Migration Failures

- Check migration logs in workflow output
- Verify database connection in `.env` file
- Test migrations manually: `python -m app.db.migrations.run_all`
- Check database permissions and connectivity
- Review migration scripts for errors

### Health Check Fails

- Check service logs: `sudo journalctl -u fastapi -f`
- Verify health endpoint manually: `curl http://44.210.144.149/api/health`
- Check database connection in `.env` file
- Review recent code changes that might break the service
- Verify migrations completed successfully

### Frontend Build Fails

- Check `VITE_API_URL` is set correctly (hardcoded to `http://44.210.144.149`)
- Verify Node.js version (18+)
- Check for TypeScript or build errors in logs

### S3 Deployment Fails

- Verify AWS credentials have S3 write permissions
- Check bucket name: `ad-mint-ai-frontend`
- Ensure bucket policy allows uploads
- Verify region: `us-east-1`

### Git Pull Fails

- Ensure EC2 instance has access to GitHub repository
- Check git remote URL is correct
- Verify SSH key or credentials are configured on EC2

## Security Best Practices

1. **Never commit secrets** - Always use GitHub Secrets
2. **Use least privilege** - Grant only necessary AWS permissions
3. **Rotate keys regularly** - Update SSH and AWS keys periodically
4. **Enable 2FA** - Protect your GitHub account
5. **Review workflow logs** - Monitor for unauthorized access
6. **Backup preservation** - Keep backups for manual recovery

## Important Notes

- **No Tests:** The workflow deploys directly without running tests (as configured)
- **Database Migrations:** All migrations in `backend/app/db/migrations/` are run automatically during deployment
- **Environment Variables:** The `.env` file on EC2 is **not modified** by the pipeline
- **Backup Retention:** Backups are preserved until next deployment (old backup is removed)
- **Migration Failures:** If migrations fail, the deployment will automatically rollback

## Support

For issues or questions:
1. Check workflow logs in GitHub Actions
2. Review deployment guide: `deployment/production/DEPLOYMENT_GUIDE.md`
3. Check service logs on EC2: `sudo journalctl -u fastapi -f`
4. Verify health endpoint: `curl http://44.210.144.149/api/health`
