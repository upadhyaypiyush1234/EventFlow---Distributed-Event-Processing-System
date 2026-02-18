# Railway.app Deployment Guide (No Credit Card Required)

Deploy EventFlow to Railway.app with $5 free credit/month - no credit card needed!

## Why Railway?

- ✅ No credit card required to start
- ✅ $5 free credit/month
- ✅ Supports full system (API + Workers + Database + Redis)
- ✅ One-click deployment from GitHub
- ✅ Auto-detects and configures everything
- ✅ Free SSL certificates

## Quick Deploy (2 Minutes)

### Step 1: Sign Up

1. Go to https://railway.app
2. Click "Login" → "Login with GitHub"
3. Authorize Railway to access your repos
4. No credit card required!

### Step 2: Deploy from GitHub

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your EventFlow repository
4. Railway will automatically detect it's a Python project

**Important:** If build fails with "Error creating build plan":
- Go to service Settings
- Under "Build", set Start Command to: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- Redeploy

### Step 3: Add Services

Railway will create the API service automatically. Now add the other services:

#### Add PostgreSQL

1. Click "+ New" in your project
2. Select "Database" → "Add PostgreSQL"
3. Railway automatically creates `DATABASE_URL` variable
4. Done! ✅

#### Add Redis

1. Click "+ New" in your project
2. Select "Database" → "Add Redis"
3. Railway automatically creates `REDIS_URL` variable
4. Done! ✅

#### Add Worker Service

1. Click "+ New" in your project
2. Select "GitHub Repo" → Choose your EventFlow repo again
3. In the service settings:
   - Name: `worker`
   - Start Command: `python -m worker.main`
   - Root Directory: `/`
4. Done! ✅

### Step 4: Initialize Database

1. Click on your PostgreSQL service
2. Click "Connect" tab
3. Copy the connection command
4. Run locally:

```bash
# Connect to Railway PostgreSQL
psql <connection-string-from-railway>

# Paste the contents of scripts/init_db.sql
# Or run:
\i scripts/init_db.sql
```

### Step 5: Test Your Deployment

1. Click on your API service
2. Click "Settings" → Copy the public URL
3. Test it:

```bash
# Replace with your Railway URL
curl https://your-app.up.railway.app/health

# View API docs
open https://your-app.up.railway.app/docs

# Send test event
curl -X POST https://your-app.up.railway.app/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "purchase",
    "user_id": "user123",
    "properties": {"amount": 99.99}
  }'
```

## Alternative: Deploy with Railway CLI

### Install Railway CLI

```bash
# macOS
brew install railway

# Linux/WSL
curl -fsSL https://railway.app/install.sh | sh

# Windows
powershell -c "irm https://railway.app/install.ps1 | iex"
```

### Deploy

```bash
# Login
railway login

# Initialize project
railway init

# Link to your project
railway link

# Deploy
railway up

# Add PostgreSQL
railway add --database postgresql

# Add Redis
railway add --database redis

# View logs
railway logs

# Open in browser
railway open
```

## Configuration

Railway automatically sets these environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `PORT` - Port for your API (Railway assigns this)

You can add custom variables in the Railway dashboard:
1. Click on a service
2. Go to "Variables" tab
3. Add variables like `LOG_LEVEL=INFO`

## Monitoring

### View Logs

```bash
# CLI
railway logs

# Or in dashboard:
# Click service → "Deployments" tab → Click deployment → View logs
```

### Check Metrics

In the Railway dashboard:
1. Click on a service
2. View CPU, Memory, Network usage
3. See deployment history

## Cost Breakdown

Railway free tier:
- ✅ $5 credit/month
- ✅ All services included
- ✅ No credit card required initially

**Estimated usage:**
- API (always on): ~$3/month
- Worker (always on): ~$2/month
- PostgreSQL: Included
- Redis: Included

**Total: ~$5/month (covered by free credit)** 🎉

## Limitations

1. **$5 credit runs out** - Good for ~1 month of demos
2. **Services sleep** - After credit runs out, services pause
3. **No auto-scaling** - Fixed resources
4. **Single region** - Can't choose region

## Optimizing for Free Tier

To make your $5 credit last longer:

### 1. Reduce Worker Replicas

In worker service settings:
- Set replicas to 1 (not 3)
- Reduces cost by 66%

### 2. Use Smaller Resources

In service settings:
- Use smallest instance size
- Disable auto-scaling

### 3. Sleep During Inactivity

Add to your API:

```python
# In api/main.py
import os

# Sleep after 15 minutes of inactivity
if os.getenv("RAILWAY_ENVIRONMENT"):
    app.add_middleware(
        # Add sleep middleware
    )
```

## Troubleshooting

### "Build Failed"

Check build logs:
1. Click service → "Deployments"
2. Click failed deployment
3. View logs

Common issues:
- Missing `requirements.txt`
- Wrong Python version
- Missing environment variables

### "Service Unhealthy"

Check health endpoint:
```bash
curl https://your-app.up.railway.app/health
```

Common issues:
- Database not initialized
- Wrong `DATABASE_URL` format
- Redis connection failed

### "Out of Credit"

Options:
1. Add credit card (still free tier, just verification)
2. Create new account with different email
3. Switch to another platform

## Updating Your Deployment

Railway auto-deploys on git push:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push

# Railway automatically deploys!
```

Or deploy manually:
```bash
railway up
```

## Custom Domain (Optional)

1. Click service → "Settings"
2. Scroll to "Domains"
3. Click "Generate Domain" (free Railway subdomain)
4. Or add custom domain (requires DNS setup)

## Useful Commands

```bash
# View all services
railway status

# Open dashboard
railway open

# View environment variables
railway variables

# Run command in Railway environment
railway run python scripts/producer.py

# Shell into service
railway shell
```

## Comparison with Other Platforms

| Feature | Railway | Render | Fly.io |
|---------|---------|--------|--------|
| Credit Card | Not required | Not required | Required |
| Free Credit | $5/month | None | None |
| Workers | ✅ Yes | ❌ No (paid) | ✅ Yes |
| Database | ✅ Included | ⚠️ 90 days | ✅ Included |
| Redis | ✅ Included | ⚠️ 90 days | ❌ External |
| Auto-deploy | ✅ Yes | ✅ Yes | ✅ Yes |
| Ease of use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

## When to Upgrade

Consider adding a credit card when:
- You need more than $5/month resources
- You want guaranteed uptime
- You need multiple environments (staging/prod)
- You want priority support

## Alternative: Render.com (API Only)

If you only want to demo the API (no workers):

1. Go to https://render.com
2. Sign up with GitHub (no credit card)
3. New → Web Service
4. Connect your repo
5. Settings:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
6. Add PostgreSQL (free for 90 days)
7. Add Redis (free for 90 days)

**Limitation:** No background workers, but API works!

## Getting Help

- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app/

## Summary

Railway.app is the best free option for EventFlow because:
1. ✅ No credit card required
2. ✅ Supports full system (API + Workers)
3. ✅ $5 free credit covers ~1 month
4. ✅ One-click deployment
5. ✅ Auto-deploys on git push

Perfect for demos, portfolio projects, and learning!

---

**Deploy now:** https://railway.app 🚀
