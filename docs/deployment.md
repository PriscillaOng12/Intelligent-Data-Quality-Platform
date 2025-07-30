# Deployment Guide

Comprehensive guide for deploying the Intelligent Data Quality Platform in production environments.

## Overview

This guide covers deployment strategies for different environments, from local development to enterprise-scale production deployments on Kubernetes. The platform is designed to be cloud-agnostic and supports deployment on AWS, Azure, GCP, and on-premises infrastructure.

---

## Quick Start (Local Development)

### Prerequisites
- Docker Desktop 4.0+
- Docker Compose 2.0+
- 8GB+ RAM available for containers
- 20GB+ disk space

### 1. Clone and Setup
```bash
git clone https://github.com/your-username/intelligent-data-quality-platform.git
cd intelligent-data-quality-platform
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` file with your settings:
```bash
# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=dataquality
POSTGRES_USER=dq_user
POSTGRES_PASSWORD=secure_password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Spark Configuration
SPARK_MASTER_URL=spark://spark-master:7077
SPARK_EXECUTOR_MEMORY=2g
SPARK_EXECUTOR_CORES=2

# API Configuration
API_SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_HOURS=24

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000/v1
```

### 3. Start Services
```bash
# Start all services
make dev-up

# Or manually with Docker Compose
docker-compose -f docker-compose.dev.yml up -d
```

### 4. Initialize Database
```bash
# Run database migrations
make db-migrate

# Load sample data (optional)
make db-seed
```

### 5. Verify Installation
```bash
# Check service health
make health-check

# Access services
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Grafana: http://localhost:3001 (admin/admin)
# Jupyter: http://localhost:8888
```

---

## Production Deployment

### Architecture Overview

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Application Load Balancer]
    end
    
    subgraph "Kubernetes Cluster"
        subgraph "Frontend Tier"
            FE1[React App Pod 1]
            FE2[React App Pod 2]
            FE3[React App Pod 3]
        end
        
        subgraph "API Tier"
            API1[FastAPI Pod 1]
            API2[FastAPI Pod 2]
            API3[FastAPI Pod 3]
        end
        
        subgraph "Processing Tier"
            SPARK[Spark Cluster]
            CELERY[Celery Workers]
        end
        
        subgraph "Data Tier"
            PG[(PostgreSQL)]
            REDIS[(Redis Cluster)]
            DELTA[(Delta Lake)]
        end
    end
    
    LB --> FE1
    LB --> FE2
    LB --> FE3
    FE1 --> API1
    FE2 --> API2
    FE3 --> API3
    API1 --> PG
    API2 --> REDIS
    API3 --> DELTA
    CELERY --> SPARK
```

### Infrastructure Requirements

#### Minimum Production Setup
- **Kubernetes Cluster**: 3 worker nodes
- **Node Specs**: 8 vCPU, 32GB RAM, 100GB SSD
- **Storage**: 1TB+ for Delta Lake, 100GB for PostgreSQL
- **Network**: 10Gbps between nodes, 1Gbps external

#### Recommended Production Setup
- **Kubernetes Cluster**: 5-10 worker nodes
- **Node Specs**: 16 vCPU, 64GB RAM, 500GB SSD
- **Storage**: 10TB+ for Delta Lake, 500GB for PostgreSQL
- **Network**: 25Gbps between nodes, 10Gbps external

---

## Kubernetes Deployment

### 1. Cluster Preparation

#### Install Required Tools
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install Terraform (for infrastructure)
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

#### Create Namespace
```bash
kubectl create namespace dataquality-platform
kubectl config set-context --current --namespace=dataquality-platform
```

### 2. Storage Configuration

#### Persistent Volumes
```yaml
# storage/postgresql-pv.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: postgresql-pv
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: fast-ssd
  hostPath:
    path: /data/postgresql
```

#### Storage Classes
```yaml
# storage/storage-class.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
allowVolumeExpansion: true
```

### 3. Secrets Management

#### Create Secrets
```bash
# Database credentials
kubectl create secret generic postgresql-secret \
  --from-literal=username=dq_user \
  --from-literal=password=secure_random_password \
  --from-literal=database=dataquality

# API secrets
kubectl create secret generic api-secret \
  --from-literal=secret-key=your-super-secret-jwt-key \
  --from-literal=database-url=postgresql://dq_user:password@postgresql:5432/dataquality

# External service credentials
kubectl create secret generic external-secrets \
  --from-literal=aws-access-key=your-aws-key \
  --from-literal=aws-secret-key=your-aws-secret \
  --from-literal=slack-webhook=your-slack-webhook
```

### 4. Database Deployment

#### PostgreSQL StatefulSet
```yaml
# manifests/postgresql.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
spec:
  serviceName: postgresql
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:15
        env:
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: database
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2"
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
```

### 5. Redis Deployment

#### Redis Cluster
```yaml
# manifests/redis.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
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
        volumeMounts:
        - name: redis-config
          mountPath: /etc/redis
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1"
      volumes:
      - name: redis-config
        configMap:
          name: redis-config
  volumeClaimTemplates:
  - metadata:
      name: redis-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 10Gi
```

### 6. Application Deployment

#### FastAPI Backend
```yaml
# manifests/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: dataquality/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: api-secret
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: api-secret
              key: secret-key
        - name: REDIS_URL
          value: "redis://redis:6379"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1"
```

#### React Frontend
```yaml
# manifests/frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: dataquality/frontend:latest
        ports:
        - containerPort: 80
        env:
        - name: REACT_APP_API_URL
          value: "https://api.dataquality-platform.com/v1"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### 7. Services and Ingress

#### Services
```yaml
# manifests/services.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

#### Ingress
```yaml
# manifests/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dataquality-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - dataquality-platform.com
    - api.dataquality-platform.com
    secretName: dataquality-tls
  rules:
  - host: dataquality-platform.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: api.dataquality-platform.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
```

---

## Helm Deployment (Recommended)

### 1. Install with Helm
```bash
# Add Helm repository
helm repo add dataquality https://charts.dataquality-platform.com
helm repo update

# Install with custom values
helm install dataquality-platform dataquality/dataquality-platform \
  --namespace dataquality-platform \
  --create-namespace \
  --values values-production.yaml
```

### 2. Custom Values File
```yaml
# values-production.yaml
global:
  environment: production
  domain: dataquality-platform.com

backend:
  replicaCount: 3
  image:
    repository: dataquality/backend
    tag: "v1.0.0"
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "4Gi"
      cpu: "2"

frontend:
  replicaCount: 3
  image:
    repository: dataquality/frontend
    tag: "v1.0.0"

postgresql:
  enabled: true
  primary:
    persistence:
      size: 100Gi
      storageClass: fast-ssd

redis:
  enabled: true
  architecture: replication
  master:
    persistence:
      size: 10Gi

spark:
  enabled: true
  master:
    resources:
      requests:
        memory: "2Gi"
        cpu: "1"
  worker:
    replicaCount: 3
    resources:
      requests:
        memory: "4Gi"
        cpu: "2"

monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
    adminPassword: secure_password

ingress:
  enabled: true
  className: nginx
  tls:
    enabled: true
    secretName: dataquality-tls
```

---

## Cloud-Specific Deployments

### AWS EKS Deployment

#### 1. Create EKS Cluster
```bash
# Using eksctl
eksctl create cluster \
  --name dataquality-cluster \
  --region us-west-2 \
  --nodegroup-name dataquality-nodes \
  --node-type m5.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed
```

#### 2. Configure Storage
```bash
# Install EBS CSI driver
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.0"

# Create storage class for GP3
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
allowVolumeExpansion: true
EOF
```

#### 3. Configure Load Balancer
```bash
# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=dataquality-cluster
```

### Azure AKS Deployment

#### 1. Create AKS Cluster
```bash
# Create resource group
az group create --name dataquality-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group dataquality-rg \
  --name dataquality-cluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-addons monitoring \
  --generate-ssh-keys
```

#### 2. Configure Storage
```bash
# Create storage class for Premium SSD
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: premium-ssd
provisioner: kubernetes.io/azure-disk
parameters:
  storageaccounttype: Premium_LRS
  kind: Managed
allowVolumeExpansion: true
EOF
```

### Google GKE Deployment

#### 1. Create GKE Cluster
```bash
gcloud container clusters create dataquality-cluster \
  --zone us-central1-a \
  --machine-type n1-standard-4 \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10
```

---

## Monitoring and Observability

### Prometheus Configuration
```yaml
# monitoring/prometheus-config.yaml
global:
  scrape_interval: 15s
scrape_configs:
- job_name: 'dataquality-backend'
  static_configs:
  - targets: ['backend-service:8000']
  metrics_path: '/metrics'
- job_name: 'dataquality-spark'
  static_configs:
  - targets: ['spark-master:8080']
```

### Grafana Dashboards
```bash
# Import pre-built dashboards
kubectl apply -f monitoring/grafana-dashboards.yaml
```

### Log Aggregation
```yaml
# logging/fluentd-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
    </source>
    
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name dataquality-logs
    </match>
```

---

## Security Configuration

### Network Policies
```yaml
# security/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dataquality-network-policy
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
```

### Pod Security Standards
```yaml
# security/pod-security.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dataquality-platform
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### RBAC Configuration
```yaml
# security/rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: dataquality-role
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dataquality-rolebinding
subjects:
- kind: ServiceAccount
  name: dataquality-service-account
roleRef:
  kind: Role
  name: dataquality-role
  apiGroup: rbac.authorization.k8s.io
```

---

## Performance Tuning

### Database Optimization
```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
SELECT pg_reload_conf();
```

### Spark Configuration
```yaml
# spark/spark-defaults.conf
spark.sql.adaptive.enabled=true
spark.sql.adaptive.coalescePartitions.enabled=true
spark.sql.adaptive.skewJoin.enabled=true
spark.serializer=org.apache.spark.serializer.KryoSerializer
spark.sql.execution.arrow.pyspark.enabled=true
spark.kubernetes.executor.deleteOnTermination=true
```

### API Performance
```yaml
# backend/performance-config.yaml
uvicorn:
  workers: 4
  worker_class: uvicorn.workers.UvicornWorker
  max_requests: 1000
  max_requests_jitter: 100
  timeout: 30
  keepalive: 2
```

---

## Backup and Disaster Recovery

### Database Backup
```bash
#!/bin/bash
# scripts/backup-database.sh
BACKUP_DIR="/backups/postgresql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

kubectl exec -n dataquality-platform postgresql-0 -- \
  pg_dump -U dq_user -h localhost dataquality | \
  gzip > "$BACKUP_DIR/dataquality_$TIMESTAMP.sql.gz"

# Keep only last 30 backups
find $BACKUP_DIR -name "dataquality_*.sql.gz" -mtime +30 -delete
```

### Delta Lake Backup
```python
# scripts/backup-deltalake.py
from delta.tables import DeltaTable
from datetime import datetime

def backup_delta_tables():
    tables = ["quality_metrics", "lineage_data", "anomaly_logs"]
    backup_path = f"s3://backup-bucket/delta-backup/{datetime.now().strftime('%Y%m%d')}"
    
    for table in tables:
        source_path = f"s3://data-lake/tables/{table}"
        target_path = f"{backup_path}/{table}"
        
        delta_table = DeltaTable.forPath(spark, source_path)
        delta_table.toDF().write.format("delta").save(target_path)

if __name__ == "__main__":
    backup_delta_tables()
```

### Automated Backup CronJob
```yaml
# manifests/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              pg_dump -h postgresql -U dq_user dataquality | \
              gzip > /backup/dataquality_$(date +%Y%m%d_%H%M%S).sql.gz
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          restartPolicy: OnFailure
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
```

---

## Troubleshooting

### Common Issues

#### Pod Startup Issues
```bash
# Check pod status
kubectl get pods -n dataquality-platform

# View pod logs
kubectl logs -f deployment/backend -n dataquality-platform

# Describe pod for events
kubectl describe pod <pod-name> -n dataquality-platform
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql -h postgresql -U dq_user -d dataquality

# Check database logs
kubectl logs -f statefulset/postgresql -n dataquality-platform
```

#### Performance Issues
```bash
# Check resource usage
kubectl top pods -n dataquality-platform

# View metrics
kubectl port-forward service/grafana 3000:3000 -n dataquality-platform
# Access Grafana at http://localhost:3000
```

### Diagnostic Commands
```bash
# Health check script
#!/bin/bash
echo "=== Cluster Status ==="
kubectl cluster-info

echo "=== Node Status ==="
kubectl get nodes

echo "=== Pod Status ==="
kubectl get pods -n dataquality-platform

echo "=== Service Status ==="
kubectl get services -n dataquality-platform

echo "=== Ingress Status ==="
kubectl get ingress -n dataquality-platform

echo "=== PVC Status ==="
kubectl get pvc -n dataquality-platform
```

---

## Scaling and Optimization

### Horizontal Pod Autoscaler
```yaml
# manifests/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 20
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
```

### Cluster Autoscaler
```yaml
# manifests/cluster-autoscaler.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  template:
    spec:
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.21.0
        name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/dataquality-cluster
```

---

## Maintenance

### Update Strategy
```yaml
# manifests/deployment-with-update-strategy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    # ... pod template
```

### Health Checks
```yaml
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
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

### Graceful Shutdown
```python
# backend/app/main.py
import signal
import sys

def signal_handler(sig, frame):
    print('Gracefully shutting down...')
    # Close database connections
    # Stop background tasks
    # Save in-progress work
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

---

This deployment guide provides comprehensive coverage for production deployments. For specific cloud providers or custom requirements, refer to the respective cloud documentation and adapt the configurations accordingly.
