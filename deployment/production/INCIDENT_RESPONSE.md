# Incident Response Procedures

This guide covers procedures for responding to production incidents.

## Incident Severity Levels

### P0 - Critical
- **Definition**: Complete service outage, data loss, security breach
- **Response Time**: Immediate (< 5 minutes)
- **Escalation**: Immediate to on-call engineer and management
- **Examples**: 
  - Application completely down
  - Database unreachable
  - Security breach detected
  - Data corruption

### P1 - High
- **Definition**: Major feature unavailable, significant performance degradation
- **Response Time**: < 15 minutes
- **Escalation**: On-call engineer within 15 minutes
- **Examples**:
  - Video generation failing
  - Authentication not working
  - API errors affecting majority of users

### P2 - Medium
- **Definition**: Partial feature degradation, minor performance issues
- **Response Time**: < 1 hour
- **Escalation**: On-call engineer within 1 hour
- **Examples**:
  - Slow API responses
  - Intermittent errors
  - Non-critical feature unavailable

### P3 - Low
- **Definition**: Minor issues, cosmetic problems
- **Response Time**: < 4 hours (business hours)
- **Escalation**: Next business day
- **Examples**:
  - UI display issues
  - Minor performance degradation
  - Non-critical bugs

## Incident Response Workflow

### 1. Detection

**Monitoring Alerts**:
- Health check endpoint failures
- Error rate spikes
- Response time degradation
- Resource utilization alerts

**User Reports**:
- Support tickets
- Error reports
- Social media mentions

### 2. Triage

**Initial Assessment**:
1. Verify incident is real (not false alarm)
2. Determine severity level
3. Identify affected components
4. Check recent deployments/changes

**Information Gathering**:
```bash
# Check health endpoint
curl http://localhost:8000/api/health

# Check service status
sudo systemctl status fastapi nginx

# Check recent logs
sudo journalctl -u fastapi -n 100

# Check system resources
htop
df -h
```

### 3. Response

**Immediate Actions**:
1. Acknowledge incident
2. Notify team (Slack, email, phone)
3. Create incident ticket
4. Begin investigation

**Investigation Steps**:
1. Review logs for errors
2. Check monitoring dashboards
3. Verify recent changes
4. Test affected functionality
5. Identify root cause

**Communication**:
- Update incident ticket with findings
- Notify stakeholders of status
- Provide estimated resolution time
- Set up status page if needed

### 4. Resolution

**Fix Implementation**:
1. Implement fix (code, configuration, infrastructure)
2. Test fix in staging (if time permits)
3. Deploy to production
4. Verify resolution

**Rollback Consideration**:
- If fix is complex or risky, consider rollback first
- See `ROLLBACK.md` for rollback procedures

### 5. Post-Incident

**Immediate Follow-up**:
1. Verify incident is fully resolved
2. Monitor for 30-60 minutes
3. Update stakeholders
4. Close incident ticket

**Post-Mortem** (within 48 hours):
1. Schedule post-mortem meeting
2. Document incident timeline
3. Identify root cause
4. Document lessons learned
5. Create action items
6. Update procedures if needed

## Incident Response Checklist

### Initial Response
- [ ] Acknowledge incident
- [ ] Determine severity level
- [ ] Notify on-call engineer
- [ ] Create incident ticket
- [ ] Gather initial information
- [ ] Check health endpoint
- [ ] Review recent logs

### Investigation
- [ ] Identify affected components
- [ ] Check monitoring dashboards
- [ ] Review recent deployments
- [ ] Test affected functionality
- [ ] Identify root cause
- [ ] Document findings

### Resolution
- [ ] Implement fix or rollback
- [ ] Test fix
- [ ] Deploy to production
- [ ] Verify resolution
- [ ] Monitor for stability

### Communication
- [ ] Update incident ticket
- [ ] Notify stakeholders
- [ ] Provide status updates
- [ ] Set up status page (if P0/P1)

### Post-Incident
- [ ] Verify full resolution
- [ ] Monitor for 30-60 minutes
- [ ] Schedule post-mortem
- [ ] Document incident
- [ ] Create action items

## Common Incident Scenarios

### Application Down

**Symptoms**: Health endpoint returns 503, no API responses

**Response**:
1. Check service status: `sudo systemctl status fastapi`
2. Check logs: `sudo journalctl -u fastapi -n 50`
3. Restart service: `sudo systemctl restart fastapi`
4. If persists, check database and S3 connectivity
5. Consider rollback if recent deployment

### Database Connection Failure

**Symptoms**: Database errors, health endpoint shows database unhealthy

**Response**:
1. Check RDS status: `aws rds describe-db-instances`
2. Verify security group rules
3. Test connection: `psql $DATABASE_URL`
4. Check network connectivity
5. Review RDS logs

### High Error Rate

**Symptoms**: Increased 500 errors, user complaints

**Response**:
1. Check error logs: `sudo journalctl -u fastapi | grep ERROR`
2. Identify error pattern
3. Check external API status (Replicate, OpenAI)
4. Review recent code changes
5. Consider rate limiting or scaling

### Performance Degradation

**Symptoms**: Slow API responses, timeout errors

**Response**:
1. Check system resources: `htop`, `df -h`
2. Check database performance
3. Review slow query logs
4. Check S3 operation times
5. Consider scaling or optimization

## Escalation Path

1. **On-Call Engineer** (First responder)
   - Initial triage and investigation
   - Attempt resolution
   - Escalate if needed

2. **DevOps Lead** (P1+ incidents)
   - Technical guidance
   - Infrastructure decisions
   - Coordinate team response

3. **Engineering Manager** (P0 incidents)
   - Business impact assessment
   - Resource allocation
   - Stakeholder communication

4. **CTO/Management** (P0 critical incidents)
   - Strategic decisions
   - External communication
   - Business continuity

## Communication Templates

### Initial Alert
```
🚨 INCIDENT ALERT - [Severity] - [Component]
Time: [Timestamp]
Status: Investigating
Impact: [Description]
Affected: [Users/Features]
```

### Status Update
```
📊 INCIDENT UPDATE - [Ticket #]
Time: [Timestamp]
Status: [Investigating/Resolved]
Progress: [Description]
ETA: [Estimated time]
```

### Resolution
```
✅ INCIDENT RESOLVED - [Ticket #]
Time: [Timestamp]
Duration: [Time]
Root Cause: [Description]
Resolution: [What was done]
Next Steps: [Follow-up actions]
```

## On-Call Rotation

- **Primary**: [Name] - [Contact]
- **Secondary**: [Name] - [Contact]
- **Schedule**: Weekly rotation
- **Handoff**: Monday 9 AM

## Tools and Resources

- **Monitoring**: [Monitoring dashboard URL]
- **Logs**: `/var/log/fastapi/app.log`, `sudo journalctl -u fastapi`
- **Incident Tracking**: [Ticketing system]
- **Communication**: Slack #incidents channel
- **Status Page**: [Status page URL]
- **Runbooks**: `deployment/production/README.md`

## Post-Mortem Template

```markdown
# Incident Post-Mortem: [Title]

**Date**: [Date]
**Duration**: [Start time] - [End time]
**Severity**: [P0/P1/P2/P3]
**Impact**: [Description]

## Timeline
- [Time]: Incident detected
- [Time]: Investigation started
- [Time]: Root cause identified
- [Time]: Fix implemented
- [Time]: Incident resolved

## Root Cause
[Detailed explanation]

## Resolution
[What was done to fix]

## Impact
- Users affected: [Number]
- Downtime: [Duration]
- Data loss: [Yes/No, details]

## Lessons Learned
- [Lesson 1]
- [Lesson 2]

## Action Items
- [ ] [Action item 1] - Owner: [Name] - Due: [Date]
- [ ] [Action item 2] - Owner: [Name] - Due: [Date]

## Prevention
[Steps to prevent recurrence]
```

## Contact Information

- **On-Call Engineer**: [Contact info]
- **DevOps Lead**: [Contact info]
- **Engineering Manager**: [Contact info]
- **AWS Support**: [Support plan details]
- **Emergency Escalation**: [Phone number]

