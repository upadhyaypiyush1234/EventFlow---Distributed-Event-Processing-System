# Render.com Deployment Guide (No Credit Card, API Only)

Deploy EventFlow API to Render.com - completely free, no credit card required!

## What You Get (Free)

- ✅ API service (750 hours/month)
- ✅ PostgreSQL database (90 days free)
- ✅ Redis (90 days free, 25MB)
- ✅ Free SSL certificate
- ✅ Auto-deploy on git push
- ❌ Background workers (requires paid plan)

**Note:** Workers won't run on free tier, but you can demo the API accepting and queuing events.

## Quick Deploy (5 Minutes)

### Step 1: Sign Up

1. Go to https://render.com
2. Click "Get Started"
3. Sign up with GitHub (no credit card needed!)
4. Authorize Render to access your repos

### Step 2: Deploy API Service

1. Click "New +" → "Web Service"
2. Connect your EventFlow repository
3. Configure:
   - **Name:** `eventflow-api`
   - **Region:** Oregon (US West) - free
   - **Branch:** `main`
   - **Root Directory:** (leave empty)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
4. Click "Create Web Service"

### Step 3: Add PostgreSQL

1. Click "New +" → "PostgreSQL"
2. Configure:
   - **Name:** `eventflow-db`
   - **Database:** `eventflow`
   - **User:** `eventflow`
   - **Region:** Same as API
   - **Instance Type:** Free
3. Click "Create Database"
4. Wait for it to provision (~2 minutes)

### Step 4: Add Redis

1. Click "New +" → "Redis"
2. Configure:
   - **Name:** `eventflow-redis`
   - **Region:** Same as API
   - **Instance Type:** Free (25MB)
3. Click "Create Redis"

### Step 5: Connect Services

1. Go to your API service
2. Click "Environment" tab
3. Add environment variables:

```
DATABASE_URL = <copy from PostgreSQL service "Internal Database URL">
REDIS_URL = <copy from Redis service "Internal Redis URL">
LOG_LEVEL = INFO
```

4. Click "Save Changes"
5. Service will auto-redeploy

### Step 6: Initialize Database

1. Go to PostgreSQL service
2. Click "Connect" → Copy the external connection string
3. Connect locally:

```bash
# Install psql if needed
brew install postgresql

# Connect to Render database
psql <connection-string-from-render>

# Run initialization script
\i scripts/init_db.sql

# Or paste the SQL content directly
# Exit
\q
```

### Step 7: Test Your API

1. Go to your API service
2. Copy the URL (looks like: `https://eventflow-api.onrender.com`)
3. Test it:

```bash
# Health check
curl https://eventflow-api.onrender.com/health

# API documentation
open https://eventflow-api.onrender.com/docs

# Send test event
curl -X POST https://eventflow-api.onrender.com/events \
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

## What Works on Free Tier

✅ **API Endpoints:**
- POST /events - Accept events
- GET /health - Health check
- GET /docs - API documentation
- GET /metrics/summary - Queue stats

✅ **Event Storage:**
- Events stored in PostgreSQL
- Events queued in Redis
- Raw events table populated

❌ **What Doesn't Work:**
- Background workers (need paid plan)
- Events won't be processed automatically
- Events stay in queue

## Workaround: Manual Processing

You can manually process queued events:

```bash
# Connect to your API service shell
# (In Render dashboard: Service → Shell)

# Run worker manually
python -m worker.main
```

Or create a cron job to process periodically (requires paid plan).

## Configuration

### Environment Variables

Set in Render dashboard (Service → Environment):

```
DATABASE_URL = <from PostgreSQL service>
REDIS_URL = <from Redis service>
LOG_LEVEL = INFO
API_HOST = 0.0.0.0
API_PORT = $PORT
```

### Auto-Deploy

Render automatically deploys when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push
# Render auto-deploys!
```

## Monitoring

### View Logs

1. Go to your service
2. Click "Logs" tab
3. View real-time logs

### Check Metrics

1. Go to your service
2. Click "Metrics" tab
3. View CPU, Memory, Bandwidth

### Health Checks

Render automatically monitors `/health` endpoint:
- Green: Service healthy
- Red: Service down (auto-restarts)

## Limitations on Free Tier

1. **Service sleeps after 15 minutes** of inactivity
   - First request after sleep takes ~30 seconds
   - Subsequent requests are fast

2. **750 hours/month** limit
   - ~31 days if always on
   - Enough for demos

3. **No background workers**
   - Can't run worker service
   - Events queue but don't process

4. **Database expires after 90 days**
   - Need to upgrade or migrate

5. **Redis expires after 90 days**
   - Need to upgrade or migrate

## Cost Breakdown

Free tier:
- API Service: **FREE** (750 hours)
- PostgreSQL: **FREE** (90 days)
- Redis: **FREE** (90 days)
- SSL Certificate: **FREE**

**Total: $0 for 90 days** 🎉

After 90 days:
- PostgreSQL: $7/month
- Redis: $10/month
- API: Still free
- **Total: $17/month**

## Upgrading to Run Workers

To run the full system with workers:

1. Upgrade to paid plan ($7/month)
2. Create worker service:
   - New → Background Worker
   - Start Command: `python -m worker.main`
   - Connect same DATABASE_URL and REDIS_URL

## Optimizing for Free Tier

### Keep Service Awake

Use a free uptime monitor:
- UptimeRobot: https://uptimerobot.com
- Ping your API every 5 minutes
- Prevents sleep

### Reduce Database Size

```python
# Add to worker/processor.py
# Delete old events periodically
async def cleanup_old_events():
    # Delete events older than 30 days
    await session.execute(
        delete(ProcessedEventDB)
        .where(ProcessedEventDB.processed_at < datetime.now() - timedelta(days=30))
    )
```

## Troubleshooting

### "Service Unavailable"

Service is sleeping. Wait 30 seconds and retry.

### "Database Connection Failed"

1. Check DATABASE_URL format
2. Verify database is running
3. Check database logs

### "Build Failed"

1. Check build logs
2. Verify requirements.txt exists
3. Check Python version compatibility

### "Health Check Failed"

1. Verify /health endpoint works locally
2. Check service logs
3. Verify environment variables set

## Custom Domain

1. Go to service → Settings
2. Scroll to "Custom Domain"
3. Add your domain
4. Update DNS records as shown
5. Free SSL certificate auto-generated

## Useful Features

### Shell Access

1. Go to service
2. Click "Shell" tab
3. Run commands in your service

```bash
# Check database connection
python -c "from common.database import check_db_health; import asyncio; print(asyncio.run(check_db_health()))"

# Check Redis connection
python -c "from common.redis_client import redis_client; import asyncio; asyncio.run(redis_client.connect()); print(asyncio.run(redis_client.check_health()))"
```

### Manual Deploys

1. Go to service
2. Click "Manual Deploy"
3. Select branch
4. Click "Deploy"

### Rollback

1. Go to service → "Events"
2. Find previous successful deploy
3. Click "Rollback"

## Comparison: Render vs Railway vs Fly.io

| Feature | Render | Railway | Fly.io |
|---------|--------|---------|--------|
| Credit Card | ❌ Not required | ❌ Not required | ✅ Required |
| Workers | ❌ Paid only | ✅ Free ($5 credit) | ✅ Free |
| Database | ⚠️ 90 days free | ✅ Included | ✅ Included |
| Redis | ⚠️ 90 days free | ✅ Included | ❌ External |
| Service Sleep | ✅ Yes (15 min) | ❌ No | ⚠️ Optional |
| Best For | API demos | Full system | Production |

## Alternative: Deploy Full System

If you need workers, consider:

1. **Railway.app** - $5 free credit, no card required
2. **Fly.io** - Requires card but won't charge
3. **Heroku** - Requires card, limited free tier

## Getting Help

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Render Status: https://status.render.com

## Summary

Render.com is perfect for:
- ✅ Demonstrating the API
- ✅ Showing event ingestion
- ✅ Portfolio projects
- ✅ Learning and testing

Not ideal for:
- ❌ Full event processing (no workers)
- ❌ Long-term production (90-day limit)
- ❌ Always-on services (sleeps after 15 min)

**For full system, use Railway.app instead!**

---

**Deploy now:** https://render.com 🚀
