# Quick Start: Deploy to Fly.io (100% Free)

Deploy EventFlow to Fly.io's free tier in under 10 minutes.

## What You'll Get (All Free)

- ✅ Live API endpoint with SSL
- ✅ Background worker processing events
- ✅ PostgreSQL database (1GB)
- ✅ Redis queue (10k commands/day)
- ✅ No credit card required
- ✅ $0/month forever

## Prerequisites

1. **GitHub account** (you have this)
2. **Fly.io account** (free signup)
3. **Upstash account** (free Redis)

## 5-Minute Setup

### 1. Install Fly CLI

**macOS:**
```bash
brew install flyctl
```

**Linux/WSL:**
```bash
curl -L https://fly.io/install.sh | sh
```

**Windows PowerShell:**
```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### 2. Sign Up & Login

```bash
flyctl auth signup
# Follow the browser prompts
```

### 3. Get Free Redis

1. Go to https://upstash.com/
2. Sign up (free, no credit card)
3. Click "Create Database"
   - Name: `eventflow`
   - Type: Regional
   - Region: US-East-1
4. Copy the Redis URL (looks like: `redis://default:xxx@xxx.upstash.io:6379`)

### 4. Run Deployment Script

```bash
cd /path/to/eventflow
./deploy-fly.sh
```

The script will:
- Create PostgreSQL database
- Deploy API service
- Deploy Worker service
- Set up everything automatically

Just follow the prompts and paste your Redis URL when asked.

### 5. Test Your API

```bash
# Your API will be at: https://eventflow-api.fly.dev

# Test health
curl https://eventflow-api.fly.dev/health

# View docs
open https://eventflow-api.fly.dev/docs

# Send test event
curl -X POST https://eventflow-api.fly.dev/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "purchase",
    "user_id": "user123",
    "properties": {"amount": 99.99, "product": "Widget"}
  }'
```

## Manual Deployment (If Script Fails)

Follow the detailed guide in [FLY_DEPLOYMENT.md](FLY_DEPLOYMENT.md)

## Common Issues

### "flyctl: command not found"

Add to PATH:
```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="$HOME/.fly/bin:$PATH"
```

### "Not logged in"

```bash
flyctl auth login
```

### "Database connection failed"

Check your DATABASE_URL format:
```
postgresql://postgres:PASSWORD@eventflow-db.internal:5432/postgres?sslmode=disable
```

### "Redis connection failed"

Verify your Upstash Redis URL includes the password:
```
redis://default:PASSWORD@HOST:PORT
```

## Monitoring

```bash
# View API logs
flyctl logs -a eventflow-api

# View worker logs
flyctl logs -a eventflow-worker

# Check status
flyctl status -a eventflow-api
flyctl status -a eventflow-worker
```

## Updating Your Code

```bash
# After making changes
git push

# Redeploy
flyctl deploy -c fly.toml
flyctl deploy -c fly.worker.toml
```

## Free Tier Limits

- 3 VMs (256MB each) ✅
- 3GB storage ✅
- 160GB bandwidth/month ✅
- Auto-sleep after inactivity (wakes on request) ⚠️

## Cost to Run

**$0/month** - Completely free!

## Need Help?

- Full guide: [FLY_DEPLOYMENT.md](FLY_DEPLOYMENT.md)
- Fly.io docs: https://fly.io/docs/
- Upstash docs: https://docs.upstash.com/

## What's Next?

1. ✅ Add your API URL to your GitHub README
2. ✅ Set up auto-deployment with GitHub Actions
3. ✅ Add a custom domain (optional, also free)
4. ✅ Share your live demo!

---

**Your EventFlow system is now live and processing events!** 🎉
