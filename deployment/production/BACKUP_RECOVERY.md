# Backup and Recovery Procedures

This guide covers backup and recovery procedures for production deployment.

## Backup Strategy

### Database Backups

**Automated Backups (RDS)**:
- **Frequency**: Daily automated backups
- **Retention**: 7-30 days (configurable)
- **Type**: Point-in-time recovery enabled
- **Location**: AWS RDS managed backups

**Manual Backup**:
```bash
# Create manual snapshot
aws rds create-db-snapshot \
    --db-instance-identifier ad-mint-ai-db \
    --db-snapshot-identifier ad-mint-ai-manual-$(date +%Y%m%d)

# List snapshots
aws rds describe-db-snapshots \
    --db-instance-identifier ad-mint-ai-db
```

### S3 Video File Backups

**Versioning**:
- S3 bucket versioning enabled
- All object versions retained
- Lifecycle policy: Transition to Standard-IA after 30 days

**Cross-Region Replication** (Optional):
```bash
# Enable cross-region replication for disaster recovery
aws s3api put-bucket-replication \
    --bucket ad-mint-ai-videos \
    --replication-configuration file://replication-config.json
```

**Manual Backup**:
```bash
# Sync to backup bucket
aws s3 sync s3://ad-mint-ai-videos/ s3://ad-mint-ai-videos-backup/ \
    --storage-class STANDARD_IA
```

### Configuration Backups

**Environment Variables**:
```bash
# Backup .env file
sudo cp /var/www/ad-mint-ai/backend/.env \
    /var/www/ad-mint-ai/backend/.env.backup.$(date +%Y%m%d)

# Backup with versioning
sudo cp /var/www/ad-mint-ai/backend/.env \
    /var/www/ad-mint-ai/backend/.env.$(date +%Y%m%d-%H%M%S)
```

**Application Code**:
- Git repository serves as code backup
- Tag releases for easy rollback
- Maintain deployment history

## Recovery Procedures

### Database Recovery

**Point-in-Time Recovery**:
```bash
# Restore to specific point in time
aws rds restore-db-instance-to-point-in-time \
    --source-db-instance-identifier ad-mint-ai-db \
    --target-db-instance-identifier ad-mint-ai-db-restored \
    --restore-time 2025-11-14T12:00:00Z

# Wait for restore
aws rds wait db-instance-available \
    --db-instance-identifier ad-mint-ai-db-restored
```

**Snapshot Recovery**:
```bash
# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier ad-mint-ai-db-restored \
    --db-snapshot-identifier ad-mint-ai-manual-20251114

# Wait for restore
aws rds wait db-instance-available \
    --db-instance-identifier ad-mint-ai-db-restored
```

**Post-Recovery Steps**:
1. Update `DATABASE_URL` in `.env` file
2. Test database connection
3. Verify data integrity
4. Restart application
5. Monitor for issues

### S3 File Recovery

**Version Recovery**:
```bash
# List object versions
aws s3api list-object-versions \
    --bucket ad-mint-ai-videos \
    --prefix videos/generation-id.mp4

# Restore specific version
aws s3api restore-object \
    --bucket ad-mint-ai-videos \
    --key videos/generation-id.mp4 \
    --version-id <version-id>
```

**Bulk Recovery from Backup**:
```bash
# Restore from backup bucket
aws s3 sync s3://ad-mint-ai-videos-backup/ s3://ad-mint-ai-videos/ \
    --storage-class STANDARD
```

### Configuration Recovery

**Environment Variables**:
```bash
# Restore from backup
sudo cp /var/www/ad-mint-ai/backend/.env.backup.20251114 \
    /var/www/ad-mint-ai/backend/.env

# Verify permissions
sudo chmod 600 /var/www/ad-mint-ai/backend/.env
sudo chown www-data:www-data /var/www/ad-mint-ai/backend/.env

# Restart application
sudo systemctl restart fastapi
```

## Disaster Recovery Plan

### Scenario 1: Complete EC2 Instance Failure

**Recovery Steps**:
1. Launch new EC2 instance (same configuration)
2. Restore application code from Git
3. Restore `.env` file from backup
4. Restore database from RDS snapshot or point-in-time
5. Update DNS records if IP changed
6. Verify all services

**Estimated Recovery Time**: 30-60 minutes

### Scenario 2: Database Corruption

**Recovery Steps**:
1. Stop application to prevent further writes
2. Create point-in-time restore
3. Verify data integrity
4. Update `DATABASE_URL` if new instance created
5. Restart application
6. Monitor for issues

**Estimated Recovery Time**: 15-30 minutes

### Scenario 3: S3 Bucket Data Loss

**Recovery Steps**:
1. Check S3 versioning for deleted objects
2. Restore from versions or backup bucket
3. Verify video files accessible
4. Update database if file paths changed
5. Test video playback

**Estimated Recovery Time**: 1-4 hours (depending on data volume)

### Scenario 4: Complete Region Failure

**Recovery Steps**:
1. Launch resources in different region
2. Restore database from cross-region backup
3. Restore S3 files from cross-region replication
4. Update DNS records
5. Update application configuration
6. Verify all services

**Estimated Recovery Time**: 2-4 hours

## Backup Verification

### Regular Backup Tests

**Monthly Tasks**:
- [ ] Test database restore from snapshot
- [ ] Test point-in-time recovery
- [ ] Verify S3 versioning works
- [ ] Test configuration restore
- [ ] Document recovery time

**Quarterly Tasks**:
- [ ] Full disaster recovery drill
- [ ] Test cross-region recovery
- [ ] Review and update backup procedures
- [ ] Verify backup retention policies

### Backup Monitoring

**Automated Checks**:
```bash
# Check RDS backup status
aws rds describe-db-instances \
    --db-instance-identifier ad-mint-ai-db \
    --query 'DBInstances[0].BackupRetentionPeriod'

# Check S3 versioning
aws s3api get-bucket-versioning \
    --bucket ad-mint-ai-videos

# Verify backup files exist
ls -lh /var/www/ad-mint-ai/backend/.env.backup.*
```

## Backup Retention Policy

| Backup Type | Retention Period | Location |
|------------|------------------|----------|
| RDS Automated Backups | 7-30 days | AWS RDS |
| RDS Manual Snapshots | 90 days | AWS RDS |
| S3 Object Versions | Indefinite | S3 Bucket |
| S3 Lifecycle (IA) | 30+ days | S3 Bucket |
| Configuration Backups | 90 days | EC2 Instance |
| Application Code | Indefinite | Git Repository |

## Recovery Testing Schedule

- **Weekly**: Verify automated backups exist
- **Monthly**: Test database restore
- **Quarterly**: Full disaster recovery drill
- **Annually**: Review and update procedures

## Contact Information

- **Database Admin**: [Contact info]
- **DevOps Lead**: [Contact info]
- **AWS Support**: [Support plan details]

## Recovery Time Objectives (RTO)

| Component | RTO | Notes |
|-----------|-----|-------|
| Database | 15 minutes | Point-in-time recovery |
| Application | 10 minutes | Code deployment |
| S3 Files | 30 minutes | Version restore |
| Full System | 60 minutes | Complete disaster recovery |

## Recovery Point Objectives (RPO)

| Component | RPO | Notes |
|-----------|-----|-------|
| Database | 5 minutes | Automated backups |
| S3 Files | Real-time | Versioning enabled |
| Configuration | 1 hour | Manual backup frequency |

