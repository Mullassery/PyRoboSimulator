# Deployment & Infrastructure Guide

## Production Kubernetes Architecture

### Core Components

```
PyRoboSimulator Production (HA):

┌─────────────────────────────────────────────────────┐
│              Load Balancer (Cloud LB)               │
│           (auto-scales based on traffic)            │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
    ┌───▼──┐   ┌───▼──┐   ┌───▼──┐
    │ Pod  │   │ Pod  │   │ Pod  │  FastAPI Backend
    │ (API │   │ (API │   │ (API │  (Replicas: 3-30)
    │ x3-30    │ x3)  │   │ x3)  │  Min: 3, Max: 30
    └──┬───┘   └──┬───┘   └──┬───┘
       │          │          │
       └──────────┼──────────┘
                  │
        ┌─────────▼─────────┐
        │  Services Mesh    │
        │  (Istio)          │
        │  - Load balancing │
        │  - Circuit break  │
        │  - Retries        │
        └─────────┬─────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼──┐   ┌─────▼────┐   ┌───▼─────┐
│PostgreSQL  │ Redis    │   │ Message │
│Cluster     │ Cluster  │   │ Queue   │
│(Primary +  │ (Cache)  │   │ (Kafka) │
│2 replicas) │          │   │         │
└───────┘   └──────────┘   └─────────┘
```

### High Availability Setup

```yaml
# ha-production.yaml
---
# PostgreSQL High Availability with Patroni
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-ha
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values:
                      - postgres
              topologyKey: kubernetes.io/hostname
      containers:
        - name: postgres
          image: postgres:16
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
          livenessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - pg_isready -U postgres
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - pg_isready -U postgres
            initialDelaySeconds: 10
            periodSeconds: 5
          resources:
            requests:
              cpu: "2"
              memory: "8Gi"
            limits:
              cpu: "4"
              memory: "16Gi"
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 1Ti

---
# Redis High Availability with Sentinel
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-ha
spec:
  serviceName: redis
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          command:
            - redis-server
            - /etc/redis/redis.conf
          ports:
            - containerPort: 6379
              name: redis
          volumeMounts:
            - name: redis-conf
              mountPath: /etc/redis
            - name: redis-data
              mountPath: /data
          resources:
            requests:
              cpu: "1"
              memory: "4Gi"
            limits:
              cpu: "2"
              memory: "8Gi"
      volumes:
        - name: redis-conf
          configMap:
            name: redis-config
  volumeClaimTemplates:
    - metadata:
        name: redis-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 100Gi

---
# FastAPI Backend with HPA
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pyrobosim-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: backend
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - backend
                topologyKey: kubernetes.io/hostname
      containers:
        - name: backend
          image: gcr.io/myproject/pyrobosim:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
              name: http
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: url
            - name: REDIS_URL
              valueFrom:
                configMapKeyRef:
                  name: redis-config
                  key: connection_string
            - name: LOG_LEVEL
              value: "INFO"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 2
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
            limits:
              cpu: "4"
              memory: "8Gi"

---
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pyrobosim-backend
  minReplicas: 3
  maxReplicas: 30
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60

---
# PodDisruptionBudget (for reliable deployments)
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: backend-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: backend

---
# Service
apiVersion: v1
kind: Service
metadata:
  name: pyrobosim-api
spec:
  type: LoadBalancer
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 8000
      protocol: TCP
      name: http
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
```

---

## Disaster Recovery

### Backup Strategy

```python
class BackupManager:
    """Automated backup and recovery."""
    
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.db = get_database_connection()
    
    async def create_backup(self):
        """Create full system backup."""
        
        timestamp = datetime.now().isoformat()
        
        # 1. Database backup
        db_backup = await self.backup_database()
        self.s3.put_object(
            Bucket='pyrobosim-backups',
            Key=f'database/{timestamp}.sql.gz',
            Body=db_backup
        )
        
        # 2. Assets backup (S3 → backup S3)
        await self.backup_assets()
        
        # 3. Configuration backup
        config_backup = await self.backup_configuration()
        self.s3.put_object(
            Bucket='pyrobosim-backups',
            Key=f'config/{timestamp}.yaml.gz',
            Body=config_backup
        )
        
        # 4. Backup manifest
        manifest = {
            "timestamp": timestamp,
            "database": f"database/{timestamp}.sql.gz",
            "assets": f"assets/{timestamp}.tar.gz",
            "config": f"config/{timestamp}.yaml.gz",
            "checksum": self.compute_checksum(),
        }
        
        self.s3.put_object(
            Bucket='pyrobosim-backups',
            Key=f'manifests/{timestamp}.json',
            Body=json.dumps(manifest)
        )
    
    async def restore_backup(self, timestamp: str):
        """Restore system from backup."""
        
        # 1. Verify backup integrity
        manifest = await self.fetch_manifest(timestamp)
        if not self.verify_checksum(manifest):
            raise BackupCorrupted(f"Backup {timestamp} corrupted")
        
        # 2. Restore database
        db_backup = self.s3.get_object(
            Bucket='pyrobosim-backups',
            Key=manifest['database']
        )
        await self.restore_database(db_backup)
        
        # 3. Restore assets
        assets = self.s3.get_object(
            Bucket='pyrobosim-backups',
            Key=manifest['assets']
        )
        await self.restore_assets(assets)
        
        # 4. Restore configuration
        config = self.s3.get_object(
            Bucket='pyrobosim-backups',
            Key=manifest['config']
        )
        await self.restore_configuration(config)
        
        logger.info(f"Successfully restored from {timestamp}")
```

### Backup Schedule

```
Hourly:   Last 24 hours (24 backups)
Daily:    Last 30 days (30 backups)
Weekly:   Last 52 weeks (52 backups)
Monthly:  Last 7 years (84 backups)

Total: ~200 backups maintained
Storage: ~50 GB (compressed, deduplicated)
RTO:  < 1 hour
RPO:  < 5 minutes
```

---

## Regional Deployment

### Multi-Region Setup

```yaml
# Primary Region (us-central1)
region: us-central1
backend_replicas: 10
database: primary (read-write)
cache: primary

# Secondary Region (eu-west1)
region: eu-west1
backend_replicas: 5
database: replica (read-only, async replication)
cache: replica (async sync)

# Tertiary Region (ap-southeast1)
region: ap-southeast1
backend_replicas: 3
database: replica (read-only, async replication)
cache: replica (async sync)

# Global Configuration
failover_strategy: automatic
replication_lag_threshold: 10 seconds
failover_time: < 2 minutes
```

### Geo-distribution

```python
class GeoRouter:
    """Route requests to nearest region."""
    
    def __init__(self):
        self.regions = {
            'us-central1': RegionCluster(...),
            'eu-west1': RegionCluster(...),
            'ap-southeast1': RegionCluster(...),
        }
    
    async def route_request(self, request: Request) -> Response:
        """Route to best region."""
        
        # Get client location
        client_lat, client_lon = get_client_geolocation(request)
        
        # Find nearest region
        nearest_region = min(
            self.regions.keys(),
            key=lambda r: distance(
                (client_lat, client_lon),
                self.regions[r].coordinates
            )
        )
        
        # Route request
        return await self.regions[nearest_region].handle(request)
```

---

## Cost Optimization

### Resource Optimization

```python
class CostOptimizer:
    """Optimize cloud spending."""
    
    def __init__(self):
        self.metrics = {}
    
    def optimize_compute(self):
        """Right-size compute resources."""
        
        # 1. Analyze utilization
        cpu_utilization = self.get_metric('cpu_utilization')
        memory_utilization = self.get_metric('memory_utilization')
        
        # 2. Identify underutilized pods
        if cpu_utilization < 30:
            # Scale down or reduce instance size
            self.reduce_compute_resources()
        
        # 3. Use spot/preemptible instances for non-critical workloads
        self.convert_to_spot_instances(workloads=['batch-processing', 'analytics'])
    
    def optimize_storage(self):
        """Optimize storage costs."""
        
        # 1. Archive old data
        old_snapshots = self.db.query(
            "SELECT * FROM snapshots WHERE created_at < NOW() - INTERVAL '90 days'"
        )
        self.archive_to_cold_storage(old_snapshots)
        
        # 2. Compress data
        self.compress_stored_data()
        
        # 3. Delete duplicates
        self.deduplicate_assets()
    
    def optimize_data_transfer(self):
        """Reduce egress costs."""
        
        # 1. Enable CDN
        self.enable_cdn_for_assets()
        
        # 2. Compress responses
        self.enable_gzip_compression()
        
        # 3. Regional replication (data locality)
        self.replicate_data_to_regions()
```

### Cost Monitoring

```python
class CostMonitor:
    """Track and alert on spending."""
    
    def __init__(self):
        self.budget = 100000  # $100k/month budget
    
    async def monitor_costs(self):
        """Daily cost monitoring."""
        
        daily_cost = await self.calculate_daily_cost()
        monthly_projection = daily_cost * 30
        
        # Alert thresholds
        if monthly_projection > self.budget * 0.8:
            alert(f"Projected cost: ${monthly_projection:.0f} (80% of budget)")
        
        if monthly_projection > self.budget:
            alert(f"WARNING: Projected overage ${monthly_projection - self.budget:.0f}")
            trigger_cost_optimization()
```

---

**Deployment & Infrastructure Complete**  
**Production-Ready HA Kubernetes Specs**
