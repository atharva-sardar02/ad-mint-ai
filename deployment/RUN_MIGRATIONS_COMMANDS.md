# Quick Migration Commands for Production

## SSH into Production

```bash
ssh -i ad-mint-ai-key.pem ubuntu@44.210.144.149
```

## Run Migrations

```bash
cd /var/www/ad-mint-ai/backend
source venv/bin/activate
python run_migrations.py
sudo systemctl restart fastapi
```

## Check What Database You're Using

```bash
# Check if using SQLite or PostgreSQL/RDS
cat /var/www/ad-mint-ai/backend/.env | grep DATABASE_URL
```

**If SQLite** (default): `DATABASE_URL=sqlite:///./ad_mint_ai.db`
**If RDS**: `DATABASE_URL=postgresql://user:pass@xxx.rds.amazonaws.com:5432/dbname`

## Verify Migrations Worked

```bash
# Check service logs
sudo journalctl -u fastapi -n 50 --no-pager

# Test health endpoint
curl http://127.0.0.1:8000/api/health
```

## If Using RDS - Test Connection

```bash
# Test PostgreSQL connection (if using RDS)
psql $DATABASE_URL
# Or manually:
# psql -h YOUR_RDS_ENDPOINT -U ad_mint_user -d ad_mint_ai
```

---

**Note:** Migrations ARE in the GitHub pipeline (`.github/workflows/deploy.yml` lines 253-260), so they should run automatically on deploy. If you're seeing errors, either:
1. Pipeline hasn't run since new migrations were added → Run commands above manually
2. Migrations failed silently → Check logs and run manually
3. Database connection issue → Check `.env` file and RDS security groups

