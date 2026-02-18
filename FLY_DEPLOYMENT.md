# Fly.io Free Tier Deployment Guide

This guide will help you deploy EventFlow on Fly.io's free tier (completely free, no credit card required initially).

## Free Tier Resources

Fly.io provides:
- ✅ 3 shared-cpu VMs (256MB RAM each)
- ✅ 3GB persistent storage
- ✅ 160GB outbound data transfer/month
- ✅ Free SSL certificates

## Architecture on Free Tier

We'll deploy:
1. **API Service** (1 VM - 256MB) - FastAPI application
2. **Worker Service** (1 VM - 256MB) - Event processor
3. **PostgreSQL** (Fly.io managed, free tier) - Database
4. **Redis** (Upstash free tier) - Message queue

Note: We'll skip Prometheus/Grafana to stay within free limits.

## Prerequisites

1. **Install Fly CLI:**

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

2. **Sign up and login:**

```bash
flyctl auth signup
# or if you have an account
flyctl auth login
```

## Step 1: Set Up PostgreSQL

Create a free PostgreSQL database:

```bash
# Create Postgres cluster (free tier: 1GB storage)
flyctl postgres create --name eventflow-db --region iad --initial-cluster-size 1 --vm-size shared-cpu-1x --volume-size 1

# Save the connection string shown - you'll need it!
# It looks like: postgres://postgres:password@eventflow-db.internal:5432
```

Save the connection details shown in the output.

## Step 2: Set Up Redis (Upstash)

Since Fly.io doesn't offer free Redis, we'll use Upstash's free tier:

1. Go to https://upstash.com/
2. Sign up (free, no credit card)
3. Create a new Redis database:
   - Name: `eventflow-redis`
   - Region: Choose closest to `iad` (US East)
   - Type: Regional
4. Copy the connection URL (format: `redis://default:password@host:port`)

## Step 3: Deploy API Service

```bash
# Navigate to your project directory
cd /path/to/eventflow

# Create the API app
flyctl apps create eventflow-api --org personal

# Set secrets (replace with your actual values)
flyctl secrets set \
  DATABASE_URL="postgresql://postgres:PASSWORD@eventflow-db.internal:5432/postgres?sslmode=disable" \
  REDIS_URL="redis://default:PASSWORD@HOST:PORT" \
  -a eventflow-api

# Deploy API
flyctl deploy -c fly.toml

# Check status
flyctl status -a eventflow-api

# View logs
flyctl logs -a eventflow-api
```

## Step 4: Initialize Database

Run the database initialization script:

```bash
# Connect to your Postgres instance
flyctl postgres connect -a eventflow-db

# Once connected, run:
\i scripts/init_db.sql

# Or copy-paste the SQL from scripts/init_db.sql
# Then exit:
\q
```

Alternatively, you can run it remotely:

```bash
# Get the connection string
flyctl postgres connect -a eventflow-db --database postgres

# In another terminal, run:
cat scripts/init_db.sql | flyctl postgres connect -a eventflow-db --database postgres
```

## Step 5: Deploy Worker Service

```bash
# Create the worker app
flyctl apps create eventflow-worker --org personal

# Set secrets (same as API)
flyctl secrets set \
  DATABASE_URL="postgresql://postgres:PASSWORD@eventflow-db.internal:5432/postgres?sslmode=disable" \
  REDIS_URL="redis://default:PASSWORD@HOST:PORT" \
  -a eventflow-worker

# Deploy worker
flyctl deploy -c fly.worker.toml

# Check status
flyctl status -a eventflow-worker

# View logs
flyctl logs -a eventflow-worker
```

## Step 6: Test Your Deployment

Get your API URL:

```bash
flyctl info -a eventflow-api
# Your URL will be: https://eventflow-api.fly.dev
```

Test the API:

```bash
# Health check
curl https://eventflow-api.fly.dev/health

# API documentation
open https://eventflow-api.fly.dev/docs

# Send a test event
curl -X POST https://eventflow-api.fly.dev/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "purchase",
    "user_id": "user123",
    "properties": {
      "amount": 99.99,
      "product": "Widget"
    }
  }'
```

## Monitoring Your Apps

```bash
# View API logs
flyctl logs -a eventflow-api

# View worker logs
flyctl logs -a eventflow-worker

# Check API status
flyctl status -a eventflow-api

# Check worker status
flyctl status -a eventflow-worker

# SSH into API container
flyctl ssh console -a eventflow-api

# Check database status
flyctl postgres status -a eventflow-db
```

## Scaling (Within Free Tier)

You have 3 free VMs total. Current setup uses 3 (1 API + 1 Worker + 1 DB).

If you want to scale workers:

```bash
# Scale workers to 2 (will use your 3rd free VM)
flyctl scale count 2 -a eventflow-worker

# Scale back to 1
flyctl scale count 1 -a eventflow-worker
```

Note: You can't scale beyond 3 total VMs on free tier.

## Troubleshooting

### API won't start

```bash
# Check logs
flyctl logs -a eventflow-api

# Common issues:
# 1. Wrong DATABASE_URL format
# 2. Redis connection failed
# 3. Database not initialized
```

### Worker not processing events

```bash
# Check worker logs
flyctl logs -a eventflow-worker

# Verify Redis connection
flyctl ssh console -a eventflow-worker
# Inside container:
python -c "import redis; r=redis.from_url('YOUR_REDIS_URL'); print(r.ping())"
```

### Database connection issues

```bash
# Test database connection
flyctl postgres connect -a eventflow-db

# Check database logs
flyctl logs -a eventflow-db
```

### Out of memory

If you see OOM errors, the 256MB might be too small. Options:

1. Reduce worker batch size in `common/config.py`
2. Optimize database connection pool size
3. Upgrade to paid tier ($1.94/month for 512MB VM)

## Cost Breakdown

Current setup on free tier:
- API VM (256MB): **FREE** (1 of 3 free VMs)
- Worker VM (256MB): **FREE** (2 of 3 free VMs)
- PostgreSQL (1GB): **FREE** (3 of 3 free VMs)
- Redis (Upstash 10k commands/day): **FREE**
- SSL certificates: **FREE**
- Bandwidth (160GB/month): **FREE**

**Total: $0/month** 🎉

## Limitations on Free Tier

1. **VMs auto-stop** after inactivity (restart on request)
2. **Limited resources** (256MB RAM per VM)
3. **No monitoring** (Prometheus/Grafana not included)
4. **Single region** (can't do multi-region)
5. **Redis limits** (10k commands/day on Upstash free)

## Upgrading If Needed

If you outgrow free tier:

```bash
# Upgrade API to 512MB ($1.94/month)
flyctl scale memory 512 -a eventflow-api

# Upgrade worker to 512MB ($1.94/month)
flyctl scale memory 512 -a eventflow-worker

# Add more workers
flyctl scale count 2 -a eventflow-worker
```

## Updating Your Deployment

When you make code changes:

```bash
# Update API
flyctl deploy -c fly.toml

# Update worker
flyctl deploy -c fly.worker.toml

# Both at once
flyctl deploy -c fly.toml && flyctl deploy -c fly.worker.toml
```

## Useful Commands

```bash
# List all your apps
flyctl apps list

# Open app in browser
flyctl open -a eventflow-api

# View app dashboard
flyctl dashboard -a eventflow-api

# Destroy an app (careful!)
flyctl apps destroy eventflow-api

# View secrets
flyctl secrets list -a eventflow-api

# Update a secret
flyctl secrets set DATABASE_URL="new-url" -a eventflow-api
```

## Environment Variables Reference

Set these secrets for both API and Worker:

```bash
DATABASE_URL="postgresql://postgres:PASSWORD@eventflow-db.internal:5432/postgres?sslmode=disable"
REDIS_URL="redis://default:PASSWORD@HOST:PORT"
```

Optional environment variables (set in fly.toml):
- `LOG_LEVEL` - Default: INFO
- `API_HOST` - Default: 0.0.0.0
- `API_PORT` - Default: 8000
- `WORKER_ID` - Default: worker-1

## Getting Help

- Fly.io Docs: https://fly.io/docs/
- Fly.io Community: https://community.fly.io/
- Upstash Docs: https://docs.upstash.com/

## Next Steps

1. ✅ Deploy and test your application
2. Add custom domain (optional, free with Fly.io)
3. Set up GitHub Actions for auto-deployment
4. Monitor logs regularly
5. Optimize for free tier limits

## Custom Domain (Optional)

```bash
# Add your domain
flyctl certs create yourdomain.com -a eventflow-api

# Add DNS records (shown in output)
# Then verify
flyctl certs show yourdomain.com -a eventflow-api
```

## GitHub Actions Auto-Deploy (Optional)

Create `.github/workflows/fly-deploy.yml`:

```yaml
name: Deploy to Fly.io

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: superfly/flyctl-actions/setup-flyctl@master
      
      - name: Deploy API
        run: flyctl deploy -c fly.toml --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
      
      - name: Deploy Worker
        run: flyctl deploy -c fly.worker.toml --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

Get your API token:
```bash
flyctl auth token
```

Add it to GitHub: Settings → Secrets → New repository secret → Name: `FLY_API_TOKEN`

---

**You're all set! Your EventFlow system is now running completely free on Fly.io.** 🚀
