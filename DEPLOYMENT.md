# Deployment Guide

Production deployment strategies for EventFlow.

## Deployment Options

1. **Docker Compose** - Simple, single-server deployment
2. **Kubernetes** - Scalable, multi-server orchestration
3. **Cloud Services** - Managed services (AWS, GCP, Azure)
4. **Hybrid** - Mix of managed and self-hosted

## Docker Compose Deployment

### Prerequisites

- Linux server with Docker installed
- Domain name (optional, for HTTPS)
- SSL certificate (optional, for HTTPS)

### Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - backend

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - backend

  api:
    image: eventflow-api:latest
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      LOG_LEVEL: INFO
      API_HOST: 0.0.0.0
      API_PORT: 8000
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - backend
      - frontend
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  worker:
    image: eventflow-worker:latest
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      LOG_LEVEL: INFO
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - backend
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    restart: unless-stopped
    networks:
      - backend

  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_USERS_ALLOW_SIGN_UP: false
      GF_SERVER_ROOT_URL: https://grafana.yourdomain.com
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
    restart: unless-stopped
    networks:
      - backend
      - frontend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
      - grafana
    restart: unless-stopped
    networks:
      - frontend

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  frontend:
  backend:
```

### Environment Variables

Create `.env.prod`:

```bash
# Database
DB_NAME=eventflow
DB_USER=eventflow
DB_PASSWORD=<strong-password>

# Redis
REDIS_PASSWORD=<strong-password>

# Grafana
GRAFANA_PASSWORD=<strong-password>

# Application
LOG_LEVEL=INFO
```

### Deployment Steps

```bash
# 1. Build images
docker-compose -f docker-compose.prod.yml build

# 2. Push to registry (optional)
docker tag eventflow-api:latest registry.example.com/eventflow-api:latest
docker push registry.example.com/eventflow-api:latest

# 3. Deploy
docker-compose -f docker-compose.prod.yml up -d

# 4. Check status
docker-compose -f docker-compose.prod.yml ps

# 5. View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- kubectl configured
- Helm (optional)

### Kubernetes Manifests

#### Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: eventflow
```

#### ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: eventflow-config
  namespace: eventflow
data:
  LOG_LEVEL: "INFO"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
```

#### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: eventflow-secrets
  namespace: eventflow
type: Opaque
stringData:
  DATABASE_URL: postgresql://user:password@postgres:5432/eventflow
  REDIS_URL: redis://:password@redis:6379
```

#### PostgreSQL Deployment

```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: eventflow
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: eventflow
        - name: POSTGRES_USER
          value: eventflow
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: eventflow-secrets
              key: DB_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: eventflow
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

#### API Deployment

```yaml
# k8s/api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: eventflow
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: eventflow-api:latest
        envFrom:
        - configMapRef:
            name: eventflow-config
        - secretRef:
            name: eventflow-secrets
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
---
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: eventflow
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### Worker Deployment

```yaml
# k8s/worker.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
  namespace: eventflow
spec:
  replicas: 5
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker
        image: eventflow-worker:latest
        envFrom:
        - configMapRef:
            name: eventflow-config
        - secretRef:
            name: eventflow-secrets
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 1Gi
```

#### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: worker-hpa
  namespace: eventflow
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: worker
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets (use real values)
kubectl create secret generic eventflow-secrets \
  --from-literal=DATABASE_URL=postgresql://... \
  --from-literal=REDIS_URL=redis://... \
  -n eventflow

# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n eventflow

# View logs
kubectl logs -f deployment/api -n eventflow
kubectl logs -f deployment/worker -n eventflow

# Scale workers
kubectl scale deployment worker --replicas=10 -n eventflow
```

## Cloud Deployments

### AWS Deployment

#### Using ECS Fargate

```bash
# 1. Create ECR repositories
aws ecr create-repository --repository-name eventflow-api
aws ecr create-repository --repository-name eventflow-worker

# 2. Build and push images
docker build -t eventflow-api -f Dockerfile.api .
docker tag eventflow-api:latest <account>.dkr.ecr.<region>.amazonaws.com/eventflow-api:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/eventflow-api:latest

# 3. Create ECS cluster
aws ecs create-cluster --cluster-name eventflow

# 4. Create task definitions (see AWS console or CLI)

# 5. Create services
aws ecs create-service \
  --cluster eventflow \
  --service-name api \
  --task-definition eventflow-api \
  --desired-count 3 \
  --launch-type FARGATE
```

#### Using EKS

```bash
# 1. Create EKS cluster
eksctl create cluster --name eventflow --region us-west-2

# 2. Deploy using kubectl
kubectl apply -f k8s/

# 3. Configure load balancer
kubectl apply -f k8s/ingress.yaml
```

#### Managed Services

- **Database:** RDS PostgreSQL
- **Cache:** ElastiCache Redis
- **Monitoring:** CloudWatch
- **Load Balancer:** ALB

### GCP Deployment

#### Using GKE

```bash
# 1. Create GKE cluster
gcloud container clusters create eventflow \
  --num-nodes=3 \
  --machine-type=n1-standard-2

# 2. Deploy
kubectl apply -f k8s/

# 3. Expose service
kubectl expose deployment api --type=LoadBalancer --port=80
```

#### Managed Services

- **Database:** Cloud SQL PostgreSQL
- **Cache:** Memorystore Redis
- **Monitoring:** Cloud Monitoring
- **Load Balancer:** Cloud Load Balancing

### Azure Deployment

#### Using AKS

```bash
# 1. Create AKS cluster
az aks create \
  --resource-group eventflow \
  --name eventflow-cluster \
  --node-count 3

# 2. Get credentials
az aks get-credentials --resource-group eventflow --name eventflow-cluster

# 3. Deploy
kubectl apply -f k8s/
```

#### Managed Services

- **Database:** Azure Database for PostgreSQL
- **Cache:** Azure Cache for Redis
- **Monitoring:** Azure Monitor
- **Load Balancer:** Azure Load Balancer

## Security Hardening

### Application Security

1. **Authentication:**
```python
# Add to api/main.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/events")
async def submit_event(
    event: Event,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify token
    verify_token(credentials.credentials)
    # Process event
```

2. **Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/events")
@limiter.limit("100/minute")
async def submit_event(request: Request, event: Event):
    # Process event
```

3. **Input Validation:**
- Already using Pydantic models
- Add custom validators for business logic
- Sanitize user inputs

### Network Security

1. **TLS/SSL:**
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    location / {
        proxy_pass http://api:8000;
    }
}
```

2. **Firewall Rules:**
```bash
# Allow only necessary ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 5432/tcp  # PostgreSQL (internal only)
ufw deny 6379/tcp  # Redis (internal only)
ufw enable
```

3. **Network Isolation:**
- Use private networks for databases
- Restrict access to monitoring tools
- Use VPN for admin access

### Database Security

1. **Connection Security:**
```python
# Use SSL for database connections
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"
```

2. **Encryption at Rest:**
- Enable PostgreSQL encryption
- Use encrypted volumes

3. **Access Control:**
- Principle of least privilege
- Separate read/write users
- Regular password rotation

## Monitoring and Alerting

### Prometheus Alerts

```yaml
# config/alerts.yml
groups:
- name: eventflow
  rules:
  - alert: HighErrorRate
    expr: rate(events_failed_total[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"
      
  - alert: HighQueueDepth
    expr: queue_depth > 10000
    for: 10m
    annotations:
      summary: "Queue depth is high"
      
  - alert: SlowProcessing
    expr: event_processing_duration_seconds{quantile="0.95"} > 1
    for: 5m
    annotations:
      summary: "Processing is slow"
```

### Grafana Dashboards

Create dashboards for:
- Event throughput
- Processing latency
- Error rates
- Queue depth
- System resources

### Log Aggregation

Use centralized logging:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Loki** (with Grafana)
- **Cloud Logging** (AWS CloudWatch, GCP Cloud Logging)

## Backup and Recovery

### Database Backups

```bash
# Automated backups
docker-compose exec postgres pg_dump -U eventflow eventflow > backup.sql

# Restore
docker-compose exec -T postgres psql -U eventflow eventflow < backup.sql

# Automated with cron
0 2 * * * docker-compose exec postgres pg_dump -U eventflow eventflow > /backups/eventflow-$(date +\%Y\%m\%d).sql
```

### Redis Backups

```bash
# Redis automatically saves to disk with AOF
# Copy backup file
docker-compose exec redis redis-cli BGSAVE
docker cp <container>:/data/dump.rdb ./backup/
```

## Scaling Strategies

### Vertical Scaling

- Increase CPU/memory for containers
- Upgrade database instance
- Increase Redis memory

### Horizontal Scaling

```bash
# Scale workers
docker-compose up -d --scale worker=10

# Kubernetes
kubectl scale deployment worker --replicas=10 -n eventflow
```

### Database Scaling

- Add read replicas
- Implement connection pooling
- Use caching layer
- Consider sharding for very large scale

## Performance Optimization

### Application Level

1. **Connection Pooling:**
```python
# Already implemented in common/database.py
engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10
)
```

2. **Batch Processing:**
```python
# Process events in batches
async def process_batch(events):
    async with get_db() as session:
        session.add_all([
            ProcessedEventDB(**event) for event in events
        ])
        await session.flush()
```

3. **Caching:**
```python
# Cache frequently accessed data
from aiocache import cached

@cached(ttl=300)
async def get_user_data(user_id):
    # Fetch user data
```

### Database Optimization

1. **Indexes:**
```sql
CREATE INDEX idx_processed_events_user_id ON processed_events(user_id);
CREATE INDEX idx_processed_events_timestamp ON processed_events(timestamp);
CREATE INDEX idx_processed_events_event_type ON processed_events(event_type);
```

2. **Partitioning:**
```sql
-- Partition by date
CREATE TABLE processed_events_2026_02 PARTITION OF processed_events
FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

## Troubleshooting Production Issues

### High CPU Usage

```bash
# Check container stats
docker stats

# Scale workers
docker-compose up -d --scale worker=5

# Check for inefficient queries
docker-compose exec postgres psql -U eventflow -c "SELECT * FROM pg_stat_activity;"
```

### High Memory Usage

```bash
# Check memory usage
docker stats

# Restart services
docker-compose restart worker

# Adjust memory limits
# Edit docker-compose.yml and add memory limits
```

### Database Connection Issues

```bash
# Check connections
docker-compose exec postgres psql -U eventflow -c "SELECT count(*) FROM pg_stat_activity;"

# Increase connection pool
# Edit common/database.py and increase pool_size
```

## Maintenance

### Updates

```bash
# 1. Pull latest code
git pull

# 2. Build new images
docker-compose build

# 3. Rolling update
docker-compose up -d --no-deps --build api
docker-compose up -d --no-deps --build worker

# 4. Verify
curl http://localhost:8000/health
```

### Database Migrations

```bash
# Use Alembic for migrations
alembic revision --autogenerate -m "Add new column"
alembic upgrade head
```

## Disaster Recovery

### Backup Strategy

- Daily database backups
- Retain backups for 30 days
- Test restore procedures monthly
- Store backups off-site

### Recovery Procedures

1. **Database Failure:**
   - Restore from latest backup
   - Replay events from raw_events table
   - Verify data integrity

2. **Complete System Failure:**
   - Deploy to new infrastructure
   - Restore database from backup
   - Restart services
   - Verify functionality

## Cost Optimization

### Resource Right-Sizing

- Monitor actual usage
- Adjust container resources
- Use spot instances (AWS)
- Scale down during low traffic

### Database Optimization

- Use appropriate instance size
- Enable auto-scaling
- Archive old data
- Use read replicas efficiently

## Compliance

### Data Retention

```sql
-- Delete old events
DELETE FROM processed_events WHERE processed_at < NOW() - INTERVAL '90 days';
DELETE FROM raw_events WHERE received_at < NOW() - INTERVAL '90 days';
```

### Audit Logging

- Log all API access
- Track data modifications
- Retain audit logs
- Regular compliance reviews

## Summary

EventFlow can be deployed in various environments:
- **Development:** Docker Compose
- **Production:** Kubernetes or managed services
- **Enterprise:** Multi-region, high availability

Key considerations:
- Security hardening
- Monitoring and alerting
- Backup and recovery
- Scaling strategies
- Cost optimization
