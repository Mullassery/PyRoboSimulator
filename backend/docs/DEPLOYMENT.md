# Deployment Guide

Complete guide for deploying PyRoboSimulator to production Kubernetes clusters.

## Prerequisites

- Kubernetes 1.24+ cluster
- kubectl configured
- Docker (for local image building)
- Helm 3+ (optional, for easier package management)
- Google Cloud SDK (if using GCP)

## Local Development

### Docker Compose

```bash
cd backend
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## Building Docker Image

### Local Build

```bash
cd backend

# Build image
docker build -t pyrobosim:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  pyrobosim:latest

# Test health
curl http://localhost:8000/health
```

### Push to Registry

```bash
# Google Container Registry
docker tag pyrobosim:latest gcr.io/your-project/pyrobosim:v0.1.0
docker push gcr.io/your-project/pyrobosim:v0.1.0

# Docker Hub
docker tag pyrobosim:latest your-username/pyrobosim:v0.1.0
docker push your-username/pyrobosim:v0.1.0
```

## Kubernetes Deployment

### Prerequisites Setup

```bash
# Create namespace
kubectl create namespace pyrobosim

# Create secrets (update with real values)
kubectl create secret generic pyrobosim-secrets \
  --from-literal=DATABASE_URL=postgresql://... \
  --from-literal=REDIS_URL=redis://... \
  --from-literal=SECRET_KEY=your-secret-key \
  -n pyrobosim

# Create postgres secret
kubectl create secret generic postgres-secret \
  --from-literal=password=change-me \
  -n pyrobosim
```

### Deploy with kubectl

```bash
cd backend/k8s

# Apply all manifests (order matters)
kubectl apply -f deployment.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f ingress.yaml

# Verify deployment
kubectl get all -n pyrobosim

# Watch rollout
kubectl rollout status deployment/pyrobosim-backend -n pyrobosim

# Port forward for local testing
kubectl port-forward svc/pyrobosim-backend 8000:8000 -n pyrobosim

# Test
curl http://localhost:8000/health
```

### Deploy with Kustomize

```bash
cd backend/k8s

# Create secrets.env with sensitive data
cat > secrets.env << EOF
DATABASE_URL=postgresql://user:password@postgres:5432/pyrobosim_prod
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-here
EOF

# Deploy
kustomize build . | kubectl apply -f -

# Update image tag
kustomize edit set image gcr.io/your-project/pyrobosim:v0.1.0
kustomize build . | kubectl apply -f -
```

### Deploy with Helm (Optional)

Create `values.yaml`:

```yaml
image:
  repository: gcr.io/your-project/pyrobosim
  tag: v0.1.0

replicas: 3

resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi

database:
  host: postgres
  port: 5432
  name: pyrobosim_prod

redis:
  host: redis
  port: 6379

ingress:
  enabled: true
  host: api.example.com
  tls: true
```

Then deploy:

```bash
helm install pyrobosim ./helm \
  -n pyrobosim \
  -f values.yaml
```

## Database Setup

### Migrate Database Schema

```bash
# Forward to PostgreSQL
kubectl port-forward svc/postgres 5432:5432 -n pyrobosim

# From another terminal, run migrations
cd backend
DATABASE_URL=postgresql://user:password@localhost:5432/pyrobosim_prod \
  alembic upgrade head
```

### Seed Initial Data (Optional)

```bash
# Create seed script
kubectl exec -it postgres-0 -n pyrobosim -- psql \
  -U pyrobosim \
  -d pyrobosim_prod \
  -c "INSERT INTO scenarios (name, world_config, published) VALUES
      ('Parking Lot', '{"bounds": {"x_min": 0, "x_max": 200}}', true);"
```

## Monitoring Setup

### Install Prometheus & Grafana

```bash
# Add Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --create-namespace

# Port forward Prometheus
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring

# Port forward Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
# Access at http://localhost:3000 (admin/prom-operator)
```

### Add PyRoboSimulator Dashboard

1. Go to Grafana → Dashboards → New → Import
2. Copy dashboard JSON from `docs/grafana-dashboard.json`
3. Select Prometheus as data source
4. Save

## Scaling

### Manual Scaling

```bash
# Scale to 10 replicas
kubectl scale deployment pyrobosim-backend \
  --replicas=10 \
  -n pyrobosim

# Verify
kubectl get pods -n pyrobosim
```

### Autoscaling

Already configured in `deployment.yaml`:
- Min replicas: 3
- Max replicas: 30
- Scale on CPU > 70% or Memory > 80%

View HPA status:

```bash
kubectl get hpa -n pyrobosim
kubectl describe hpa pyrobosim-backend-hpa -n pyrobosim
```

## Health Checks

### Liveness Probe

Tests if pod should be restarted:
- Endpoint: `GET /health`
- Initial delay: 10 seconds
- Period: 10 seconds
- Timeout: 5 seconds
- Failure threshold: 3

### Readiness Probe

Tests if pod can accept traffic:
- Endpoint: `GET /ready`
- Initial delay: 5 seconds
- Period: 5 seconds
- Timeout: 3 seconds
- Failure threshold: 2

### Manual Health Check

```bash
kubectl exec -it deployment/pyrobosim-backend -n pyrobosim -- \
  curl http://localhost:8000/health
```

## Logs & Debugging

### View Logs

```bash
# All backend pods
kubectl logs -f deployment/pyrobosim-backend -n pyrobosim

# Specific pod
kubectl logs -f pyrobosim-backend-xyz -n pyrobosim

# Last 100 lines
kubectl logs --tail=100 deployment/pyrobosim-backend -n pyrobosim

# Timestamps
kubectl logs -f deployment/pyrobosim-backend --timestamps -n pyrobosim
```

### Connect to Pod

```bash
# Interactive shell
kubectl exec -it pyrobosim-backend-xyz -n pyrobosim -- /bin/sh

# Run command
kubectl exec pyrobosim-backend-xyz -n pyrobosim -- curl http://localhost:8000/health
```

### Port Forward for Debugging

```bash
# API
kubectl port-forward svc/pyrobosim-backend 8000:8000 -n pyrobosim

# Metrics
kubectl port-forward svc/pyrobosim-backend 8001:8001 -n pyrobosim

# PostgreSQL
kubectl port-forward svc/postgres 5432:5432 -n pyrobosim

# Redis
kubectl port-forward svc/redis 6379:6379 -n pyrobosim
```

## Updates & Rollbacks

### Rolling Update

```bash
# Set new image
kubectl set image deployment/pyrobosim-backend \
  backend=gcr.io/your-project/pyrobosim:v0.2.0 \
  -n pyrobosim \
  --record

# Watch progress
kubectl rollout status deployment/pyrobosim-backend -n pyrobosim

# View history
kubectl rollout history deployment/pyrobosim-backend -n pyrobosim
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/pyrobosim-backend \
  -n pyrobosim

# Rollback to specific revision
kubectl rollout undo deployment/pyrobosim-backend \
  --to-revision=2 \
  -n pyrobosim
```

## Backup & Recovery

### Backup PostgreSQL

```bash
# Backup to local file
kubectl exec -it postgres-0 -n pyrobosim -- \
  pg_dump -U pyrobosim pyrobosim_prod > backup.sql

# Backup with compression
kubectl exec -it postgres-0 -n pyrobosim -- \
  pg_dump -U pyrobosim -Fc pyrobosim_prod > backup.dump
```

### Restore PostgreSQL

```bash
# Restore from SQL
kubectl exec -i postgres-0 -n pyrobosim -- \
  psql -U pyrobosim pyrobosim_prod < backup.sql

# Restore from dump
kubectl exec -i postgres-0 -n pyrobosim -- \
  pg_restore -U pyrobosim -d pyrobosim_prod < backup.dump
```

## Network Policies

Default network policies restrict traffic:
- Ingress: Only from ingress-nginx
- Egress: Only to PostgreSQL, Redis, external services

View:

```bash
kubectl get networkpolicies -n pyrobosim
kubectl describe networkpolicy pyrobosim-backend -n pyrobosim
```

## Security

### Pod Security Policy

Enforced policies:
- Non-root user (UID 1000)
- Read-only filesystem
- No privilege escalation
- Dropped ALL capabilities

View:

```bash
kubectl get psp
kubectl describe psp restricted
```

### RBAC

Service account created with minimal permissions. View:

```bash
kubectl get serviceaccount -n pyrobosim
kubectl get rolebinding -n pyrobosim
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n pyrobosim

# Check events
kubectl get events -n pyrobosim --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n pyrobosim
```

### Database connection issues

```bash
# Test connectivity
kubectl run -it --rm debug --image=postgres:16-alpine --restart=Never -- \
  psql -h postgres -U pyrobosim -d pyrobosim_prod -c "SELECT 1"

# Check service DNS
kubectl exec -it <pod-name> -- nslookup postgres.pyrobosim.svc.cluster.local
```

### High latency

```bash
# Check resource usage
kubectl top pods -n pyrobosim
kubectl top nodes

# Check HPA
kubectl get hpa -n pyrobosim
kubectl describe hpa pyrobosim-backend-hpa -n pyrobosim

# Check metrics
kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/pyrobosim/pods/*/cpu_usage
```

## Performance Tuning

### Resource Limits

Adjust in `deployment.yaml`:

```yaml
resources:
  requests:
    cpu: "500m"      # Guaranteed allocation
    memory: "512Mi"
  limits:
    cpu: "2000m"     # Maximum allowed
    memory: "2Gi"
```

### Replica Count

Adjust `replicas` field or HPA `minReplicas`/`maxReplicas`.

### Database Connections

Adjust in config:

```yaml
DATABASE_POOL_MIN_SIZE: "5"
DATABASE_POOL_MAX_SIZE: "20"
```

## SLA Monitoring

Target: 99.95% uptime

Track:
- Pod uptime: `kubectl uptime` plugin
- Service availability: Prometheus alerts
- Error rate: < 1% from metrics
- P99 latency: < 500ms from metrics

---

**Deployment Guide Complete**

For questions or issues, refer to:
- Kubernetes docs: https://kubernetes.io/docs/
- Kustomize: https://kustomize.io/
- Helm: https://helm.sh/
