# AWS Architecture - Quick Reference

**Last Updated:** 2025-11-15

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────┐
│   Users     │
│  Browsers   │
└──────┬──────┘
       │
       ├─────────────────────────────────┐
       │                                 │
       ▼                                 ▼
┌──────────────┐              ┌──────────────────┐
│  S3 Frontend │              │   EC2 Backend    │
│  (Static)    │              │   (API Only)     │
│              │              │                  │
│ ad-mint-ai-  │              │  ┌────────────┐ │
│ frontend      │              │  │  Nginx    │ │
│              │              │  │  Port 80  │ │
│ Static Website│             │  └─────┬──────┘ │
│ Hosting       │             │        │        │
└──────────────┘             │        ▼        │
                             │  ┌────────────┐ │
                             │  │  FastAPI   │ │
                             │  │  Port 8000 │ │
                             │  └─────┬──────┘ │
                             └────────┼────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │  RDS         │  │  S3 Videos   │  │  External   │
            │  PostgreSQL  │  │  Storage     │  │  APIs       │
            │  (Private)   │  │              │  │              │
            └──────────────┘  └──────────────┘  └──────────────┘
```

## Component Locations

| Component | Service | Location/Details |
|-----------|---------|------------------|
| **Frontend** | S3 | `ad-mint-ai-frontend` bucket - Static website hosting |
| **Backend API** | EC2 | Ubuntu 22.04, FastAPI on port 8000 |
| **Web Server** | EC2 | Nginx on port 80 (API proxy only) |
| **Database** | RDS | PostgreSQL in private subnet |
| **Video Storage** | S3 | `ad-mint-ai-videos` bucket |
| **Environment** | EC2 | `.env` file on instance |
| **Logging** | EC2 | Log files with rotation |

## Network Flow

1. **Frontend Request:**
   - User → HTTP → S3 Website Endpoint → React App

2. **API Request:**
   - React App → HTTP → Nginx (EC2) → FastAPI → Response

3. **Backend Operations:**
   - FastAPI → RDS (database queries)
   - FastAPI → S3 (video upload/download)
   - FastAPI → External APIs (Replicate, OpenAI)

## Security Groups

**EC2:**
- Port 80 (HTTP) - Open to Internet (API requests)
- Port 22 (SSH) - Your IP only
- Port 8000 - localhost only

**RDS:**
- Port 5432 - EC2 Security Group only (private)

**S3:**
- Frontend bucket: Public read access
- Video bucket: EC2 IAM role access only

## Key Files

- **Full Architecture Diagram:** `docs/aws-architecture-diagram.md`
- **Story Details:** `docs/sprint-artifacts/1-5-production-deployment.md`
- **Context:** `docs/sprint-artifacts/1-5-production-deployment.context.xml`

## Deployment Summary

- ✅ Frontend: S3 static website hosting
- ✅ Backend: EC2 with FastAPI + Nginx
- ✅ Database: RDS PostgreSQL (private subnet)
- ✅ Storage: S3 for videos
- ✅ Secrets: `.env` file on EC2
- ✅ Logging: File-based on EC2
- ❌ No CloudFront (removed)
- ❌ No SSL/TLS (removed)
- ❌ No Secrets Manager (removed)
- ❌ No CloudWatch (removed)



