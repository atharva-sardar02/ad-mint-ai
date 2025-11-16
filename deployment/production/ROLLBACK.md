# Rollback Procedures

This guide covers procedures for rolling back deployments when issues are detected.

## Prerequisites

- SSH access to EC2 instance
- Git access to repository
- AWS CLI configured (for S3 rollback)
- Database backup available (for database rollback)

## Rollback Strategies

### 1. Code Rollback (Git-based)

**When to use**: Application code issues, bugs, or feature regressions

**Procedure**:

```bash
# SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Navigate to deployment directory
cd /var/www/ad-mint-ai

# Check current commit
git log -1

# List recent commits to find rollback target
git log --oneline -10

# Rollback to previous commit (replace <commit-hash> with target)
git checkout <commit-hash>

# Pull dependencies if needed
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart fastapi
sudo systemctl reload nginx

# Verify rollback
curl http://localhost:8000/api/health
```

**Verification**:
- Health endpoint returns 200
- Application functionality restored
- No errors in logs

### 2. Frontend Rollback (S3)

**When to use**: Frontend issues, UI bugs, or broken features

**Procedure**:

```bash
# List S3 object versions (if versioning enabled)
aws s3api list-object-versions \
    --bucket ad-mint-ai-frontend \
    --prefix index.html

# Restore previous version
aws s3api restore-object \
    --bucket ad-mint-ai-frontend \
    --key index.html \
    --version-id <previous-version-id>

# Or deploy previous build from local
cd frontend
git checkout <previous-commit>
npm run build
aws s3 sync dist/ s3://ad-mint-ai-frontend/ --delete
```

**Verification**:
- Frontend loads correctly
- No console errors
- Features work as expected

### 3. Database Rollback

**When to use**: Database migration issues, data corruption, or schema problems

**Procedure**:

```bash
# Stop application to prevent new writes
sudo systemctl stop fastapi

# Create point-in-time restore from RDS backup
aws rds restore-db-instance-to-point-in-time \
    --source-db-instance-identifier ad-mint-ai-db \
    --target-db-instance-identifier ad-mint-ai-db-restored \
    --restore-time 2025-11-14T12:00:00Z  # Use actual restore time

# Wait for restore to complete
aws rds wait db-instance-available \
    --db-instance-identifier ad-mint-ai-db-restored

# Update DATABASE_URL in .env file
# Point to restored instance endpoint

# Restart application
sudo systemctl start fastapi

# Verify data integrity
psql $DATABASE_URL -c "SELECT COUNT(*) FROM generations;"
```

**Note**: Point-in-time restore creates a new RDS instance. Update DNS or connection string accordingly.

### 4. Configuration Rollback

**When to use**: Environment variable issues, configuration errors

**Procedure**:

```bash
# Backup current .env file
sudo cp /var/www/ad-mint-ai/backend/.env /var/www/ad-mint-ai/backend/.env.backup

# Restore previous .env file
sudo cp /var/www/ad-mint-ai/backend/.env.previous /var/www/ad-mint-ai/backend/.env

# Verify permissions
sudo chmod 600 /var/www/ad-mint-ai/backend/.env
sudo chown www-data:www-data /var/www/ad-mint-ai/backend/.env

# Restart application
sudo systemctl restart fastapi

# Verify configuration
curl http://localhost:8000/api/health
```

### 5. Full System Rollback

**When to use**: Multiple component failures, major deployment issues

**Procedure**:

```bash
# 1. Stop all services
sudo systemctl stop fastapi nginx

# 2. Rollback code
cd /var/www/ad-mint-ai
git checkout <previous-commit>

# 3. Rollback frontend (if needed)
cd frontend
git checkout <previous-commit>
npm run build
aws s3 sync dist/ s3://ad-mint-ai-frontend/ --delete

# 4. Rollback database (if needed)
# Follow database rollback procedure above

# 5. Rollback configuration (if needed)
# Follow configuration rollback procedure above

# 6. Restart services
sudo systemctl start fastapi nginx

# 7. Verify all components
curl http://localhost:8000/api/health
```

## Rollback Decision Matrix

| Issue Type | Rollback Strategy | Estimated Time |
|------------|------------------|----------------|
| Application bug | Code rollback | 5-10 minutes |
| Frontend issue | Frontend rollback | 5-10 minutes |
| Database issue | Database rollback | 15-30 minutes |
| Configuration error | Configuration rollback | 5 minutes |
| Multiple issues | Full system rollback | 30-60 minutes |

## Pre-Rollback Checklist

- [ ] Identify root cause of issue
- [ ] Determine rollback target (commit, version, timestamp)
- [ ] Verify backup availability
- [ ] Notify team of rollback plan
- [ ] Document issue and rollback reason
- [ ] Prepare rollback procedure
- [ ] Test rollback in staging (if time permits)

## Post-Rollback Checklist

- [ ] Verify application functionality
- [ ] Check health endpoint
- [ ] Review logs for errors
- [ ] Test critical user flows
- [ ] Monitor for 15-30 minutes
- [ ] Document rollback in incident log
- [ ] Schedule post-mortem meeting
- [ ] Update deployment procedures if needed

## Rollback Automation

For faster rollbacks, consider implementing:

1. **Deployment tags**: Tag each deployment with version number
2. **Automated backups**: Automatic database and configuration backups before deployment
3. **Blue-green deployment**: Maintain two environments for instant rollback
4. **Rollback scripts**: Automated scripts for common rollback scenarios

## Emergency Contacts

- **DevOps Lead**: [Contact info]
- **Database Admin**: [Contact info]
- **AWS Support**: [Support plan details]

## Rollback Log Template

```
Date: [Date/Time]
Rolled back from: [Commit/Version]
Rolled back to: [Commit/Version]
Reason: [Issue description]
Performed by: [Name]
Duration: [Time taken]
Impact: [User impact]
Resolution: [How issue was resolved]
Follow-up: [Actions needed]
```

## Prevention

To minimize rollback frequency:

1. **Staging environment**: Always test in staging first
2. **Gradual rollout**: Deploy to small percentage of users first
3. **Feature flags**: Use feature flags for new features
4. **Monitoring**: Set up alerts for critical metrics
5. **Automated testing**: Comprehensive test suite before deployment
6. **Database migrations**: Test migrations in staging, use backward-compatible migrations

