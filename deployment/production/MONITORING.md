# Monitoring and Observability Guide

This guide covers monitoring setup and procedures for production deployment.

## Monitoring Strategy

### Health Checks

**Endpoint**: `GET /api/health`

**Response Format**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-14T12:00:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "type": "postgresql"
    },
    "storage": {
      "status": "healthy",
      "type": "s3",
      "bucket": "ad-mint-ai-videos"
    },
    "external_apis": {
      "replicate": {
        "status": "configured",
        "token_set": true
      },
      "openai": {
        "status": "configured",
        "key_set": true
      }
    }
  }
}
```

**Monitoring Frequency**: Every 1-5 minutes

### Log Monitoring

**Log Locations**:
- FastAPI: `/var/log/fastapi/app.log`
- Nginx Access: `/var/log/nginx/ad-mint-ai-access.log`
- Nginx Error: `/var/log/nginx/ad-mint-ai-error.log`
- Systemd Journal: `sudo journalctl -u fastapi`

**Log Levels**:
- **ERROR**: Application errors, failures
- **WARNING**: Potential issues, degraded functionality
- **INFO**: Normal operations, important events
- **DEBUG**: Detailed debugging information (development only)

### System Resource Monitoring

**Key Metrics**:
- CPU usage: `top`, `htop`
- Memory usage: `free -h`
- Disk usage: `df -h`
- Network: `iftop`, `netstat`

**Thresholds**:
- CPU: Alert if > 80% for 5 minutes
- Memory: Alert if > 85% usage
- Disk: Alert if > 80% usage
- Disk I/O: Monitor for bottlenecks

## Manual Monitoring Commands

### Health Check

```bash
# Check health endpoint
curl http://localhost:8000/api/health | jq

# Check from external
curl https://api.yourdomain.com/api/health | jq
```

### Service Status

```bash
# Check FastAPI service
sudo systemctl status fastapi

# Check Nginx service
sudo systemctl status nginx

# Check all services
sudo systemctl status fastapi nginx
```

### Log Monitoring

```bash
# View recent FastAPI logs
sudo journalctl -u fastapi -n 50 --no-pager

# Follow FastAPI logs
sudo journalctl -u fastapi -f

# View application log file
tail -f /var/log/fastapi/app.log

# View Nginx access logs
tail -f /var/log/nginx/ad-mint-ai-access.log

# View Nginx error logs
tail -f /var/log/nginx/ad-mint-ai-error.log

# Search logs for errors
sudo journalctl -u fastapi | grep ERROR

# Search logs for specific generation
sudo journalctl -u fastapi | grep "generation-id"
```

### System Resources

```bash
# CPU and memory usage
htop

# Disk usage
df -h

# Memory usage
free -h

# Disk I/O
iostat -x 1

# Network connections
netstat -tulpn | grep :8000

# Process information
ps aux | grep uvicorn
```

### Database Monitoring

```bash
# Check database connection
psql $DATABASE_URL -c "SELECT version();"

# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('ad_mint_ai'));"

# Check table sizes
psql $DATABASE_URL -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### S3 Monitoring

```bash
# Check S3 bucket
aws s3 ls s3://ad-mint-ai-videos/

# Check bucket size
aws s3 ls s3://ad-mint-ai-videos/ --recursive --human-readable --summarize

# Check S3 access
aws s3 ls s3://ad-mint-ai-videos/videos/ | head -10
```

## Automated Monitoring Setup

### Option 1: AWS CloudWatch

**Setup**:
1. Install CloudWatch agent on EC2
2. Configure log groups
3. Set up alarms for metrics

**Metrics to Monitor**:
- CPU utilization
- Memory utilization
- Disk usage
- Network in/out
- Application errors
- Health check failures

### Option 2: Prometheus + Grafana

**Setup**:
1. Install Prometheus on monitoring server
2. Configure FastAPI metrics endpoint
3. Set up Grafana dashboards
4. Configure alerts

### Option 3: Third-Party Services

**Options**:
- Datadog
- New Relic
- Sentry (error tracking)
- Pingdom (uptime monitoring)

## Alerting Configuration

### Critical Alerts (P0)

- Health endpoint down (> 2 minutes)
- Database connection failure
- Application service stopped
- Disk space > 95%

### High Priority Alerts (P1)

- Error rate > 5% for 5 minutes
- Response time > 5 seconds
- CPU usage > 90% for 10 minutes
- Memory usage > 90%

### Medium Priority Alerts (P2)

- Error rate > 1% for 15 minutes
- Response time > 2 seconds
- Disk space > 85%
- S3 upload failures

## Log Rotation

**Configuration**: `/etc/logrotate.d/fastapi`

**Settings**:
- Rotate daily
- Keep 30 days of logs
- Compress old logs
- Create new log files with proper permissions

**Manual Rotation**:
```bash
# Force log rotation
sudo logrotate -f /etc/logrotate.d/fastapi

# Check log rotation status
sudo logrotate -d /etc/logrotate.d/fastapi
```

## Performance Monitoring

### API Response Times

**Monitor**:
- Average response time
- P95 response time
- P99 response time
- Timeout rate

**Tools**:
- Nginx access logs
- Application logs
- APM tools

### Database Performance

**Monitor**:
- Query execution time
- Connection pool usage
- Slow queries
- Lock contention

**Commands**:
```bash
# Check slow queries
psql $DATABASE_URL -c "
SELECT 
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

## Incident Detection

### Automated Checks

**Script**: `deployment/monitoring/health-check.sh`

```bash
#!/bin/bash
# Health check script for monitoring

HEALTH_URL="http://localhost:8000/api/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" != "200" ]; then
    echo "ALERT: Health check failed (HTTP $RESPONSE)"
    exit 1
fi

# Check component health
HEALTH_JSON=$(curl -s $HEALTH_URL)
STATUS=$(echo $HEALTH_JSON | jq -r '.status')

if [ "$STATUS" != "healthy" ]; then
    echo "ALERT: Health status is $STATUS"
    exit 1
fi

echo "OK: Health check passed"
exit 0
```

**Cron Job**:
```bash
# Run every 5 minutes
*/5 * * * * /path/to/health-check.sh
```

## Monitoring Dashboard

### Key Metrics to Display

1. **System Health**
   - Overall status (healthy/degraded/unhealthy)
   - Component status (database, storage, APIs)
   - Uptime percentage

2. **Performance**
   - Request rate
   - Response time (avg, p95, p99)
   - Error rate
   - Throughput

3. **Resources**
   - CPU usage
   - Memory usage
   - Disk usage
   - Network I/O

4. **Application Metrics**
   - Active generations
   - Completed generations
   - Failed generations
   - Average generation time
   - Cost per generation

5. **Infrastructure**
   - RDS connection count
   - S3 request rate
   - EC2 instance status

## Best Practices

1. **Log Everything Important**: But not too much (avoid log spam)
2. **Set Realistic Thresholds**: Based on actual usage patterns
3. **Test Alerts**: Ensure alerts work and are actionable
4. **Document Procedures**: For responding to each alert type
5. **Review Regularly**: Update monitoring based on incidents
6. **Use Structured Logging**: JSON format for easier parsing
7. **Monitor External Dependencies**: Replicate, OpenAI API status
8. **Track Business Metrics**: User activity, generation success rate

## Contact Information

- **Monitoring Team**: [Contact info]
- **On-Call Engineer**: [Contact info]
- **DevOps Lead**: [Contact info]

