# EventFlow Quick Start Guide

Get EventFlow up and running in minutes!

## Prerequisites

### Required
- **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
  - Windows: Docker Desktop for Windows
  - Mac: Docker Desktop for Mac
  - Linux: Docker Engine + Docker Compose

### Optional (for testing scripts)
- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **pip** - Python package manager (included with Python)

## Installation

### Windows

#### Step 1: Install Docker Desktop

1. Download Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Run the installer
3. Restart your computer
4. Start Docker Desktop
5. Wait for Docker to be ready (whale icon in system tray)

#### Step 2: Run Setup Script

Open PowerShell in the project directory:

```powershell
.\setup_windows.ps1
```

This script will:
- Check Docker installation
- Start all services
- Wait for health checks
- Display service URLs
- Run a test event

#### Step 3: Verify Installation

The script will show you:
- ✅ Service status
- 🌐 Access URLs
- 📊 Test results

### Linux/Mac

#### Step 1: Install Docker

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER
```

**Mac:**
```bash
brew install --cask docker
# Start Docker Desktop from Applications
```

#### Step 2: Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Step 3: Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","timestamp":"...","services":{...}}
```

## Manual Setup (All Platforms)

If you prefer manual control:

```bash
# 1. Start services
docker-compose up -d

# 2. Check all services are running
docker-compose ps

# 3. Wait for health checks (30-60 seconds)
docker-compose logs -f api

# 4. Test the API
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "page_view",
    "user_id": "user123",
    "properties": {"page": "/home"}
  }'
```

## Accessing Services

Once running, access these URLs:

### Core Services
- **API Documentation:** http://localhost:8000/docs
- **API Health Check:** http://localhost:8000/health
- **API Root:** http://localhost:8000/

### Monitoring
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000
  - Username: `admin`
  - Password: `admin`

### Databases (for direct access)
- **PostgreSQL:** `localhost:5432`
  - Database: `eventflow`
  - User: `eventflow`
  - Password: `eventflow_pass`
- **Redis:** `localhost:6379`

## Testing the System

### Method 1: Interactive API (Easiest)

1. Open http://localhost:8000/docs
2. Click on `POST /events`
3. Click "Try it out"
4. Modify the example JSON:
```json
{
  "event_type": "purchase",
  "user_id": "user123",
  "properties": {
    "amount": 99.99,
    "product": "Widget"
  }
}
```
5. Click "Execute"
6. See the response!

### Method 2: PowerShell Script (Windows)

```powershell
.\send_test_event.ps1
```

### Method 3: Python Scripts

#### Install Python dependencies:
```bash
pip install -r requirements.txt
```

#### Send test events:
```bash
# Send 10 events
python scripts/producer.py --count 10

# Send 100 events
python scripts/producer.py --count 100

# Send events continuously
python scripts/producer.py --count 1000 --rate 10
```

#### Monitor processing:
```bash
python scripts/monitor.py
```

#### Run load test:
```bash
python scripts/load_test.py --events 1000 --rate 100
```

### Method 4: cURL (Linux/Mac/Windows)

```bash
# Send a page view event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "page_view",
    "user_id": "user123",
    "properties": {"page": "/home", "referrer": "google"}
  }'

# Send a purchase event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "purchase",
    "user_id": "user456",
    "properties": {"amount": 149.99, "product": "Premium Widget"}
  }'

# Send a user signup event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user_signup",
    "user_id": "user789",
    "properties": {"email": "user@example.com", "plan": "free"}
  }'
```

## Viewing Results

### Check API Metrics

```bash
curl http://localhost:8000/metrics/summary
```

Response:
```json
{
  "queue_length": 0,
  "pending_messages": 0,
  "timestamp": "2026-02-17T00:00:00"
}
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker

# Last 100 lines
docker-compose logs --tail=100 worker
```

### Query Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U eventflow -d eventflow

# View processed events
SELECT event_id, event_type, user_id, processed_at 
FROM processed_events 
ORDER BY processed_at DESC 
LIMIT 10;

# View failed events
SELECT event_id, error_message, failed_at 
FROM failed_events 
ORDER BY failed_at DESC;

# Exit
\q
```

### Check Prometheus Metrics

1. Open http://localhost:9090
2. Try these queries:
   - `events_received_total` - Total events received
   - `events_processed_total` - Total events processed
   - `rate(events_processed_total[1m])` - Events per second
   - `event_processing_duration_seconds` - Processing latency

### View Grafana Dashboards

1. Open http://localhost:3000
2. Login: admin / admin
3. Skip password change (or set new password)
4. Add Prometheus data source:
   - Go to Configuration → Data Sources
   - Add Prometheus
   - URL: `http://prometheus:9090`
   - Save & Test

## Common Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Stop and remove volumes (clean slate)
docker-compose down -v

# View status
docker-compose ps

# View resource usage
docker stats
```

### Scaling Workers

```bash
# Scale to 5 workers
docker-compose up -d --scale worker=5

# Scale to 1 worker
docker-compose up -d --scale worker=1

# Check worker count
docker-compose ps worker
```

### Debugging

```bash
# View logs with timestamps
docker-compose logs -f --timestamps

# Follow specific service
docker-compose logs -f api

# Execute command in container
docker-compose exec api bash
docker-compose exec postgres psql -U eventflow

# Inspect container
docker-compose exec api env
```

## Troubleshooting

### Docker not starting

**Windows:**
- Ensure Hyper-V is enabled
- Restart Docker Desktop
- Check Windows Services for Docker

**Mac:**
- Restart Docker Desktop
- Check disk space
- Reset Docker to factory defaults if needed

**Linux:**
- `sudo systemctl start docker`
- `sudo systemctl status docker`
- Check logs: `journalctl -u docker`

### Services not healthy

```bash
# Check service status
docker-compose ps

# View logs for failing service
docker-compose logs api
docker-compose logs postgres

# Restart specific service
docker-compose restart api

# Rebuild and restart
docker-compose up -d --build
```

### Port already in use

```bash
# Find process using port (Windows)
netstat -ano | findstr :8000

# Find process using port (Linux/Mac)
lsof -i :8000

# Kill process or change port in docker-compose.yml
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Reset database (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
```

### Redis connection errors

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Restart Redis
docker-compose restart redis
```

### Worker not processing events

```bash
# Check worker logs
docker-compose logs -f worker

# Check queue length
curl http://localhost:8000/metrics/summary

# Restart workers
docker-compose restart worker

# Scale up workers
docker-compose up -d --scale worker=3
```

### Python script errors

```bash
# Install dependencies
pip install -r requirements.txt

# Use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Performance Testing

### Load Test

```bash
# Install dependencies
pip install -r requirements.txt

# Run load test
python scripts/load_test.py --events 10000 --rate 100

# Monitor during test
python scripts/monitor.py
```

### Expected Performance

- **Throughput:** 1000+ events/second
- **Latency:** P95 < 100ms
- **Success Rate:** 99.9%+

### Monitoring Performance

```bash
# Watch metrics in real-time
watch -n 1 'curl -s http://localhost:8000/metrics/summary'

# View Prometheus metrics
open http://localhost:9090

# Check resource usage
docker stats
```

## Next Steps

### Learn More
- Read **ARCHITECTURE.md** for system design details
- Read **TESTING.md** for testing strategies
- Read **INTERVIEW_GUIDE.md** for interview prep

### Customize
- Modify event types in `common/models.py`
- Add validation logic in `worker/processor.py`
- Create Grafana dashboards
- Add custom metrics

### Deploy
- Read **DEPLOYMENT.md** for production deployment
- Set up CI/CD pipeline
- Configure monitoring and alerting
- Implement authentication

## Getting Help

### Check Logs
```bash
docker-compose logs -f
```

### Check Health
```bash
curl http://localhost:8000/health
```

### Common Issues
- Ensure Docker is running
- Check port availability
- Verify network connectivity
- Review service logs

### Resources
- Docker Documentation: https://docs.docker.com/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Redis Streams: https://redis.io/docs/data-types/streams/

## Clean Up

### Stop Services
```bash
docker-compose down
```

### Remove All Data
```bash
docker-compose down -v
```

### Remove Images
```bash
docker-compose down --rmi all -v
```

---

**You're all set! Start sending events and watch them flow through the system.**
