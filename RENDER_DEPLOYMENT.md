# Deploying EventFlow to Render

This guide walks you through deploying EventFlow to Render.com.

## Prerequisites

- GitHub account with your EventFlow repository
- Render account (free tier works)

## Architecture on Render

```
┌─────────────────────────────────────────┐
│           Render Services               │
├─────────────────────────────────────────┤
│  Web Service (API)                      │
│  - FastAPI application                  │
│  - Auto-scaling                         │
│  - HTTPS enabled                        │
├─────────────────────────────────────────┤
│  Background Worker (optional)           │
│  - Event processing                     │
│  - Scalable instances                   │
├─────────────────────────────────────────┤
│  PostgreSQL Database                    │
│  - Managed PostgreSQL                   │
│  - Automatic backups                    │
├─────────────────────────────────────────┤
│  Redis Instance                         │
│  - Managed Redis                        │
│  - SSL/TLS enabled                      │
└─────────────────────────────────────────┘
```

## Step 1: Create PostgreSQL Database

1. Go to Render Dashboard
2. Click "New +" → "PostgreSQL"
3. Configure:
   - **Name**: `eventflow-db`
   - **Database**: `eventflow`
   - **User**: `eventflow`
   - **Region**: Choose closest to you
   - **Plan**: Free (or paid for production)
4. Click "Create Database"
5. **Save the Internal Database URL** (starts with `postgresql://`)

## Step 2: Create Redis Instance

1. Click "New +" → "Redis"
2. Configure:
   - **Name**: `eventflow-redis`
   - **Region**: Same as database
   - **Plan**: Free (or paid for production)
   - **Maxmemory Policy**: `allkeys-lru`
3. Click "Create Redis"
4. **Save the Internal Redis URL** (starts with `redis://` or `rediss://`)

## Step 3: Deploy API Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `eventflow-api`
   - **Region**: Same as database/Redis
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn api.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Free (or paid for production)

4. **Environment Variables** (click "Advanced" → "Add Environment Variable"):
   ```
   DATABASE_URL=<your-postgres-internal-url>
   REDIS_URL=<your-redis-internal-url>
   LOG_LEVEL=INFO
   PYTHON_VERSION=3.11.9
   ```

5. Click "Create Web Service"

## Step 4: Deploy Worker Service (Optional)

1. Click "New +" → "Background Worker"
2. Connect same GitHub repository
3. Configure:
   - **Name**: `eventflow-worker`
   - **Region**: Same as others
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     python -m worker.main
     ```
   - **Plan**: Free (or paid for production)

4. **Environment Variables**:
   ```
   DATABASE_URL=<your-postgres-internal-url>
   REDIS_URL=<your-redis-internal-url>
   LOG_LEVEL=INFO
   WORKER_ID=worker-render-1
   PYTHON_VERSION=3.11.9
   ```

5. Click "Create Background Worker"

## Environment Variables Explained

### Required Variables

- **DATABASE_URL**: PostgreSQL connection string
  - Format: `postgresql://user:password@host:port/database`
  - Get from Render PostgreSQL dashboard (Internal Database URL)
  
- **REDIS_URL**: Redis connection string
  - Format: `redis://default:password@host:port` or `rediss://...` (with SSL)
  - Get from Render Redis dashboard (Internal Redis URL)

### Optional Variables

- **LOG_LEVEL**: Logging level (DEBUG, INFO, WARNING, ERROR)
  - Default: `INFO`
  - Use `DEBUG` for troubleshooting

- **WORKER_ID**: Unique identifier for worker
  - Default: `worker-1`
  - Use different IDs for multiple workers

- **PYTHON_VERSION**: Python version to use
  - Default: `3.11.9`
  - Render uses this to install correct Python

## Troubleshooting

### Issue: Redis Connection Error

**Error**: `Connection closed by server` or `Authentication failed`

**Solutions**:

1. **Check Redis URL format**:
   - Should start with `redis://` or `rediss://` (SSL)
   - Render Redis requires SSL, use `rediss://`

2. **Update Redis URL**:
   ```bash
   # If URL is redis://, change to rediss://
   REDIS_URL=rediss://default:password@host:port
   ```

3. **Check Redis is running**:
   - Go to Render Redis dashboard
   - Ensure status is "Available"

4. **Verify environment variable**:
   - Go to Web Service → Environment
   - Check REDIS_URL is set correctly
   - Click "Save Changes" if modified

### Issue: Database Connection Error

**Error**: `could not connect to server` or `password authentication failed`

**Solutions**:

1. **Use Internal Database URL**:
   - Go to PostgreSQL dashboard
   - Copy "Internal Database URL" (not External)
   - Internal URLs work within Render network

2. **Check database is running**:
   - PostgreSQL status should be "Available"
   - Wait a few minutes after creation

3. **Verify connection string**:
   ```
   postgresql://user:password@host:port/database
   ```

### Issue: Application Won't Start

**Error**: `Application startup failed`

**Solutions**:

1. **Check logs**:
   - Go to Web Service → Logs
   - Look for specific error messages

2. **Verify build succeeded**:
   - Check "Events" tab
   - Ensure "Build succeeded" message

3. **Check Python version**:
   - Add `PYTHON_VERSION=3.11.9` to environment variables

4. **Verify start command**:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```

### Issue: Port Binding Error

**Error**: `Address already in use`

**Solution**:
- Render automatically sets `$PORT` environment variable
- Always use `--port $PORT` in start command
- Don't hardcode port 8000

### Issue: Module Not Found

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solutions**:

1. **Check requirements.txt**:
   - Ensure all dependencies are listed
   - Include version numbers

2. **Rebuild service**:
   - Go to Web Service → Manual Deploy
   - Click "Clear build cache & deploy"

## Testing Your Deployment

### 1. Check API Health

```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-18T...",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  },
  "version": "1.0.0"
}
```

### 2. Send Test Event

```bash
curl -X POST https://your-app.onrender.com/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "purchase",
    "user_id": "test_user",
    "properties": {"amount": 99.99, "product": "Test"}
  }'
```

Expected response:
```json
{
  "event_id": "...",
  "status": "accepted",
  "message": "Event accepted for processing",
  "received_at": "..."
}
```

### 3. Check API Documentation

Visit: `https://your-app.onrender.com/docs`

### 4. View Logs

```bash
# In Render dashboard
# Go to Web Service → Logs
# Or Background Worker → Logs
```

## Scaling on Render

### Horizontal Scaling (Multiple Instances)

1. Go to Web Service → Settings
2. Scroll to "Scaling"
3. Increase "Instance Count"
4. Click "Save Changes"

**Note**: Free tier limited to 1 instance

### Vertical Scaling (More Resources)

1. Go to Web Service → Settings
2. Change "Instance Type" to higher tier
3. Click "Save Changes"

## Monitoring

### Built-in Monitoring

Render provides:
- CPU usage
- Memory usage
- Request count
- Response times

Access: Web Service → Metrics

### Application Metrics

EventFlow exposes Prometheus metrics:
- `https://your-app.onrender.com/metrics/summary`

### Logs

Structured JSON logs available in:
- Web Service → Logs
- Background Worker → Logs

Search by:
- `correlation_id` - trace specific event
- `level: ERROR` - find errors
- `event_type` - filter by event type

## Cost Optimization

### Free Tier Limits

- **Web Service**: 750 hours/month (sleeps after 15 min inactivity)
- **PostgreSQL**: 1GB storage, 97 hours/month
- **Redis**: 25MB storage
- **Background Worker**: 750 hours/month

### Tips

1. **Use free tier for demos**:
   - Sufficient for portfolio projects
   - Services sleep when inactive (wake on request)

2. **Upgrade for production**:
   - Paid plans don't sleep
   - More resources and storage
   - Better performance

3. **Monitor usage**:
   - Check Render dashboard for usage
   - Set up billing alerts

## Production Checklist

Before going to production:

- [ ] Use paid plans (no sleep)
- [ ] Enable automatic backups (PostgreSQL)
- [ ] Set up custom domain
- [ ] Enable HTTPS (automatic on Render)
- [ ] Add authentication to API
- [ ] Implement rate limiting
- [ ] Set up monitoring/alerting
- [ ] Configure log retention
- [ ] Test failure scenarios
- [ ] Document runbooks

## Render-Specific Configuration

### render.yaml (Infrastructure as Code)

Create `render.yaml` in your repo:

```yaml
services:
  - type: web
    name: eventflow-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: eventflow-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: eventflow-redis
          property: connectionString
      - key: LOG_LEVEL
        value: INFO
      - key: PYTHON_VERSION
        value: 3.11.9

  - type: worker
    name: eventflow-worker
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python -m worker.main
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: eventflow-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: eventflow-redis
          property: connectionString
      - key: LOG_LEVEL
        value: INFO
      - key: WORKER_ID
        value: worker-render-1

databases:
  - name: eventflow-db
    databaseName: eventflow
    user: eventflow

  - name: eventflow-redis
    plan: starter
```

## Support

### Render Documentation
- https://render.com/docs

### EventFlow Issues
- Check logs in Render dashboard
- Review error messages
- Test locally with same environment variables

### Common Issues
- Redis SSL: Use `rediss://` not `redis://`
- Database: Use Internal URL not External
- Port: Always use `$PORT` variable
- Python: Specify version in environment

## Next Steps

1. **Add Custom Domain**:
   - Go to Settings → Custom Domain
   - Follow DNS configuration steps

2. **Set Up Monitoring**:
   - Integrate with external monitoring (Datadog, New Relic)
   - Set up alerts for errors

3. **Implement CI/CD**:
   - Render auto-deploys on git push
   - Add GitHub Actions for tests before deploy

4. **Scale Workers**:
   - Add more background workers for higher throughput
   - Each worker processes events in parallel

---

**Your EventFlow is now running on Render! 🚀**

Access your API at: `https://your-app-name.onrender.com`
