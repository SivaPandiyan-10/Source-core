# JobSearchEngine - Deployment Guide

## Overview

This guide covers deploying JobSearchEngine in production environments, including containerized deployment, systemd services on Linux, and scheduled tasks on Windows.

## Prerequisites

- Built binaries (see [BUILD.md](BUILD.md))
- Target system with appropriate permissions
- Log directory with write access
- Network access to job portals

## 1. Local Deployment

### Linux/macOS

Create a deployment directory:

```bash
mkdir -p ~/jobsearch/{bin,config,resumes,logs,cache}
cp JobSearchEngine/bin/jobsearch_app ~/jobsearch/bin/
cp JobSearchEngine/bin/jobsearch_engine ~/jobsearch/bin/
cp JobSearchEngine/config/config.yaml ~/jobsearch/config/
cp JobSearchEngine/resumes/*.txt ~/jobsearch/resumes/
chmod +x ~/jobsearch/bin/*
```

Run manually:
```bash
~/jobsearch/bin/jobsearch_app --candidate "John Doe" --config ~/jobsearch/config/config.yaml
```

### Windows

Create deployment folder:
```powershell
mkdir C:\jobsearch\{bin,config,resumes,logs,cache} -ErrorAction SilentlyContinue
Copy-Item "JobSearchEngine\bin\*" "C:\jobsearch\bin\"
Copy-Item "JobSearchEngine\config\config.yaml" "C:\jobsearch\config\"
Copy-Item "JobSearchEngine\resumes\*.txt" "C:\jobsearch\resumes\"
```

Run manually:
```powershell
C:\jobsearch\bin\jobsearch_app.exe --candidate "John Doe" --config C:\jobsearch\config\config.yaml
```

## 2. Systemd Service (Linux)

Create service file `/etc/systemd/system/jobsearch.service`:

```ini
[Unit]
Description=JobSearchEngine - Job Search Automation
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=jobsearch
WorkingDirectory=/opt/jobsearch
ExecStart=/opt/jobsearch/bin/jobsearch_app --candidate "John Doe" --config /opt/jobsearch/config/config.yaml

# Restart policy
Restart=on-failure
RestartSec=10
StartLimitInterval=60s
StartLimitBurst=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jobsearch

# Resource limits
MemoryLimit=500M
CPUQuota=50%

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/jobsearch/logs /opt/jobsearch/cache

[Install]
WantedBy=multi-user.target
```

Setup and run:
```bash
# Create jobsearch user
sudo useradd -r -s /bin/false jobsearch

# Copy files to /opt/jobsearch
sudo mkdir -p /opt/jobsearch/{bin,config,resumes,logs,cache}
sudo cp JobSearchEngine/bin/* /opt/jobsearch/bin/
sudo cp JobSearchEngine/config/config.yaml /opt/jobsearch/config/
sudo cp JobSearchEngine/resumes/*.txt /opt/jobsearch/resumes/

# Set permissions
sudo chown -R jobsearch:jobsearch /opt/jobsearch
sudo chmod 750 /opt/jobsearch/bin/*

# Register and start service
sudo systemctl daemon-reload
sudo systemctl enable jobsearch
sudo systemctl start jobsearch

# Check status
sudo systemctl status jobsearch
sudo journalctl -u jobsearch -f  # Follow logs
```

## 3. Scheduled Tasks (Windows)

### Via Task Scheduler GUI

1. Open Task Scheduler
2. Create Basic Task → "JobSearchEngine"
3. Trigger: Daily at 6:00 AM
4. Action: Start program
   - Program: `C:\jobsearch\bin\jobsearch_app.exe`
   - Arguments: `--candidate "John Doe" --config C:\jobsearch\config\config.yaml`
   - Start in: `C:\jobsearch`
5. Conditions: Run even if idle, Run whether logged in or not

### Via PowerShell Script

```powershell
# Create scheduled task via PowerShell
$taskName = "JobSearchEngine"
$program = "C:\jobsearch\bin\jobsearch_app.exe"
$args = '--candidate "John Doe" --config C:\jobsearch\config\config.yaml'
$workingDir = "C:\jobsearch"

# Create action
$action = New-ScheduledTaskAction -Execute $program -Argument $args -WorkingDirectory $workingDir

# Create trigger (daily at 6 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At 6am

# Create settings
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfIdle:$false -MultipleInstances IgnoreNew

# Register task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest

# Verify
Get-ScheduledTask -TaskName $taskName | fl
```

### Via schtasks Command

```cmd
schtasks /create /tn "JobSearchEngine" /tr "C:\jobsearch\bin\jobsearch_app.exe --candidate ^"John Doe^" --config C:\jobsearch\config\config.yaml" /sc daily /st 06:00
```

## 4. Docker Deployment

### Dockerfile

```dockerfile
FROM golang:1.21-alpine AS builder-go
FROM alpine:3.18 AS builder-cpp

WORKDIR /build
RUN apk add --no-cache cmake build-base g++

COPY JobSearchEngine/cpp ./cpp
COPY JobSearchEngine/CMakeLists.txt .
RUN mkdir build && cd build && cmake .. && make

# Final image
FROM alpine:3.18
RUN apk add --no-cache ca-certificates
RUN adduser -D jobsearch

WORKDIR /app
COPY --from=builder-cpp /build/bin/jobsearch_engine /app/bin/
COPY --from=builder-go /go/bin/jobsearch /app/bin/
COPY JobSearchEngine/config /app/config
COPY JobSearchEngine/resumes /app/resumes

RUN chown -R jobsearch:jobsearch /app
USER jobsearch

ENTRYPOINT ["/app/bin/jobsearch_app"]
CMD ["--candidate", "John Doe", "--config", "/app/config/config.yaml"]
```

### Build and Run

```bash
# Build image
docker build -t jobsearch:1.0.0 .

# Run container
docker run -d \
  --name jobsearch \
  --restart unless-stopped \
  -v /path/to/logs:/app/logs \
  -v /path/to/config:/app/config \
  jobsearch:1.0.0 \
  --candidate "John Doe"

# View logs
docker logs -f jobsearch

# Stop
docker stop jobsearch
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  jobsearch:
    build: .
    container_name: jobsearch
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config:ro
      - ./resumes:/app/resumes:ro
      - ./cache:/app/cache
    environment:
      - RUST_LOG=info
    command:
      - --candidate
      - "John Doe"
      - --config
      - /app/config/config.yaml
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 500M
        reservations:
          cpus: '0.25'
          memory: 256M
```

Run with Docker Compose:
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## 5. Kubernetes Deployment

### StatefulSet Configuration

Create `jobsearch-deployment.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: jobsearch-config
data:
  config.yaml: |
    job_search:
      enabled: true
      interval_hours: 6
      min_confidence_threshold: 0.65
    # ... rest of config

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: jobsearch
spec:
  serviceName: jobsearch
  replicas: 1
  selector:
    matchLabels:
      app: jobsearch
  template:
    metadata:
      labels:
        app: jobsearch
    spec:
      containers:
      - name: jobsearch
        image: jobsearch:1.0.0
        imagePullPolicy: IfNotPresent
        args:
          - --candidate
          - "John Doe"
          - --config
          - /etc/jobsearch/config.yaml
        volumeMounts:
        - name: config
          mountPath: /etc/jobsearch
          readOnly: true
        - name: logs
          mountPath: /app/logs
        - name: resumes
          mountPath: /app/resumes
          readOnly: true
        - name: cache
          mountPath: /app/cache
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "500Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - test
            - -f
            - /app/logs/$(date +%Y-%m-%d).log
          initialDelaySeconds: 60
          periodSeconds: 300
      volumes:
      - name: config
        configMap:
          name: jobsearch-config
      - name: resumes
        configMap:
          name: jobsearch-resumes
  volumeClaimTemplates:
  - metadata:
      name: logs
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
  - metadata:
      name: cache
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 5Gi
```

Deploy to Kubernetes:
```bash
kubectl apply -f jobsearch-deployment.yaml
kubectl get statefulset jobsearch
kubectl logs -f jobsearch-0
```

## 6. Monitoring and Logging

### Log Rotation (Linux)

Create `/etc/logrotate.d/jobsearch`:

```
/opt/jobsearch/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 jobsearch jobsearch
    sharedscripts
}
```

Run logrotate:
```bash
logrotate /etc/logrotate.d/jobsearch
```

### Health Checks

Bash script to verify service:
```bash
#!/bin/bash

LOG_FILE="/opt/jobsearch/logs/$(date +%Y-%m-%d).log"

# Check if service is running
if ! systemctl is-active jobsearch > /dev/null; then
    echo "ERROR: jobsearch service is not running"
    exit 1
fi

# Check if log file exists and was recently updated
if [ ! -f "$LOG_FILE" ]; then
    echo "ERROR: Log file not found: $LOG_FILE"
    exit 1
fi

LAST_UPDATE=$(stat -f%m "$LOG_FILE" 2>/dev/null || stat -c%Y "$LOG_FILE")
CURRENT_TIME=$(date +%s)
TIME_DIFF=$((CURRENT_TIME - LAST_UPDATE))

# Alert if no activity in 12 hours
if [ $TIME_DIFF -gt 43200 ]; then
    echo "WARN: No job search activity for 12 hours"
    exit 2
fi

echo "OK: jobsearch is running normally"
exit 0
```

### Alert Configuration

Monitor with Prometheus/AlertManager:

```yaml
groups:
- name: jobsearch
  rules:
  - alert: JobSearchDown
    expr: up{job="jobsearch"} == 0
    for: 5m
    annotations:
      summary: "JobSearchEngine is down"
  
  - alert: JobSearchHighErrorRate
    expr: rate(jobsearch_errors_total[5m]) > 0.05
    for: 10m
    annotations:
      summary: "High error rate detected"
```

## 7. Configuration Management

### Environment-Specific Configs

```
config/
├── config.yaml              # Default
├── config.production.yaml   # Production
├── config.staging.yaml      # Staging
└── config.development.yaml  # Development
```

Load based on environment:
```bash
ENVIRONMENT=${ENVIRONMENT:-production}
CONFIG_FILE="config/config.${ENVIRONMENT}.yaml"
./bin/jobsearch_app --candidate "John Doe" --config "$CONFIG_FILE"
```

### Secrets Management

Use environment variables for sensitive data:

```bash
# Set API keys (if needed in future)
export LINKEDIN_API_KEY="..."
export NAUKRI_API_KEY="..."

./bin/jobsearch_app --candidate "John Doe" --config config/config.yaml
```

## 8. Backup and Recovery

### Backup Script

```bash
#!/bin/bash
BACKUP_DIR="/backup/jobsearch"
SOURCE_DIR="/opt/jobsearch"

mkdir -p "$BACKUP_DIR"

# Backup logs (daily)
tar czf "$BACKUP_DIR/logs-$(date +%Y%m%d).tar.gz" "$SOURCE_DIR/logs/"

# Backup config (weekly)
if [ $(date +%u) -eq 1 ]; then
    tar czf "$BACKUP_DIR/config-$(date +%Y%m%d).tar.gz" "$SOURCE_DIR/config/"
fi

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

Schedule with cron:
```bash
0 2 * * * /opt/jobsearch/backup.sh
```

## 9. Troubleshooting Deployment

### Service Won't Start

```bash
# Check logs
sudo journalctl -u jobsearch -n 50

# Test configuration
/opt/jobsearch/bin/jobsearch_app --candidate "Test" --config /opt/jobsearch/config/config.yaml

# Check permissions
ls -la /opt/jobsearch/{bin,config,logs}
```

### High Memory Usage

```bash
# Check process
ps aux | grep jobsearch

# Kill and restart
sudo systemctl restart jobsearch
```

### No Log Entries

```bash
# Verify log directory
ls -la /opt/jobsearch/logs/

# Check for errors
sudo systemctl status jobsearch -l
sudo journalctl -u jobsearch --all
```

---

For more details, see [BUILD.md](BUILD.md) and [ARCHITECTURE.md](ARCHITECTURE.md).
