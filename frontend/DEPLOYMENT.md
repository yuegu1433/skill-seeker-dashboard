# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Skill Seekers Frontend application in various environments using Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Options](#deployment-options)
- [Configuration](#configuration)
- [Production Deployment](#production-deployment)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Prerequisites

### System Requirements

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher (or `docker compose` plugin)
- **Memory**: Minimum 2GB RAM, recommended 4GB+
- **Disk Space**: Minimum 10GB free space
- **CPU**: Minimum 2 cores, recommended 4+ cores
- **Network**: Internet connection for pulling images

### Check Prerequisites

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version
# or
docker compose version

# Check Docker daemon
docker info
```

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd skillseekers-frontend

# Copy environment file
cp .env.example .env

# Edit environment variables (optional)
nano .env
```

### 2. Build and Deploy

```bash
# Make deployment script executable
chmod +x deploy.sh

# Build the application
./deploy.sh build

# Deploy the application
./deploy.sh deploy

# Check status
./deploy.sh status
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **API**: http://localhost:3000/api
- **Health Check**: http://localhost:3000/health

## Deployment Options

### Option 1: Development Deployment

For local development with hot reloading:

```bash
# Start development services
docker-compose -f docker-compose.yml --profile dev up -d

# View logs
docker-compose logs -f frontend-dev
```

### Option 2: Production Deployment

For production environments:

```bash
# Deploy with health checks
./deploy.sh --env production deploy

# Or manually
docker-compose up -d
```

### Option 3: Full Stack Deployment

With all services (backend, database, Redis, etc.):

```bash
# Start all services
docker-compose --profile full-stack up -d

# Check all services
docker-compose ps
```

### Option 4: With Monitoring

Enable Prometheus and Grafana:

```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana: http://localhost:3001
# Access Prometheus: http://localhost:9090
```

### Option 5: With Load Balancer

For high availability:

```bash
# Start with load balancer
docker-compose --profile loadbalancer up -d

# Access via load balancer: http://localhost:8080
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for all options):

```bash
# Application
VITE_APP_VERSION=1.0.0
NODE_ENV=production

# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Ports
FRONTEND_PORT=3000
NGINX_PORT=80
```

### Custom Configuration

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Modify values**:
   ```bash
   nano .env
   ```

3. **Use environment-specific configs**:
   ```bash
   # Production
   ./deploy.sh --env production deploy

   # Staging
   ./deploy.sh --env staging deploy
   ```

### Nginx Configuration

Customize nginx behavior by editing:

- `nginx.conf` - Main nginx configuration
- `docker/nginx-default.conf` - Server configuration

### Docker Compose Profiles

Available profiles:

- **default**: Frontend only
- **dev**: Development services
- **full-stack**: All services (backend, db, redis, etc.)
- **monitoring**: Monitoring stack (Prometheus, Grafana)
- **loadbalancer**: Load balancer configuration

Usage:
```bash
docker-compose --profile <profile-name> up -d
```

## Production Deployment

### 1. Prepare for Production

```bash
# Set production environment
export ENVIRONMENT=production

# Create production environment file
cp .env.example .env.production
nano .env.production
```

### 2. Configure SSL/TLS

Edit `docker/nginx-proxy.conf` and uncomment SSL section:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # ... rest of configuration
}
```

### 3. Deploy with Rollback Support

```bash
# Deploy with automatic rollback on failure
./deploy.sh --rollback --force deploy

# Monitor deployment
./deploy.sh logs
```

### 4. Health Checks

```bash
# Run health check
./deploy.sh health

# Check container status
./deploy.sh status
```

### 5. Scale Application

```bash
# Scale frontend service
docker-compose up -d --scale frontend=3

# Check scaling
docker-compose ps
```

### 6. Update Application

```bash
# Build new version
./deploy.sh build

# Deploy with zero downtime
./deploy.sh deploy

# Rollback if needed
./deploy.sh rollback
```

## Monitoring and Health Checks

### Health Check Endpoints

- **Health Check**: `GET /health`
- **Readiness Probe**: `GET /ready`
- **Docker Health**: `GET /docker-health`

### Container Health Monitoring

```bash
# Check container health
docker-compose ps

# View health check logs
docker logs <container-name>

# Manual health check
docker exec <container-name> /usr/local/bin/healthcheck.sh
```

### Resource Monitoring

```bash
# View resource usage
docker stats

# Check disk usage
df -h

# Monitor logs
./deploy.sh logs
```

### Performance Monitoring

Enable monitoring profile:

```bash
# Start monitoring
docker-compose --profile monitoring up -d

# Access Grafana: http://localhost:3001
# Default credentials: admin/admin

# Access Prometheus: http://localhost:9090
```

### Log Management

```bash
# View logs
./deploy.sh logs

# View specific service logs
./deploy.sh logs frontend

# Follow logs
./deploy.sh logs -f

# Export logs
docker-compose logs > application.log
```

## Troubleshooting

### Common Issues

#### 1. Container Fails to Start

**Symptoms**: Container exits immediately

**Solution**:
```bash
# Check logs
docker logs <container-name>

# Check configuration
docker exec <container-name> nginx -t

# Run health check
./deploy.sh health
```

#### 2. API Connection Failed

**Symptoms**: Frontend loads but API calls fail

**Solution**:
```bash
# Check API URL in .env
grep VITE_API_URL .env

# Test API connectivity
curl http://localhost:8000/health

# Check nginx configuration
docker exec <container-name> cat /etc/nginx/nginx.conf
```

#### 3. WebSocket Connection Failed

**Symptoms**: Real-time features not working

**Solution**:
```bash
# Check WebSocket URL
grep VITE_WS_URL .env

# Test WebSocket connection
wscat -c ws://localhost:8000/ws

# Check nginx WebSocket config
docker exec <container-name> cat /etc/nginx/nginx.conf | grep -A 10 "location /ws"
```

#### 4. High Memory Usage

**Symptoms**: Container crashes with OOM error

**Solution**:
```bash
# Check memory usage
docker stats --no-stream

# Adjust resource limits in docker-compose.yml
# Reduce nginx worker processes
export NGINX_WORKER_PROCESSES=1
```

#### 5. Slow Response Time

**Symptoms**: Application loads slowly

**Solution**:
```bash
# Enable compression
# Check nginx configuration

# Optimize cache headers
# Check CDN configuration

# Monitor performance
docker stats
```

#### 6. SSL/TLS Issues

**Symptoms**: HTTPS not working

**Solution**:
```bash
# Check certificate paths
ls -la /etc/nginx/ssl/

# Verify certificate
openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout

# Test SSL configuration
docker exec <container-name> nginx -t
```

### Debug Mode

Enable debug logging:

```bash
# Set debug environment
export LOG_LEVEL=debug
export VITE_DEBUG=true

# Restart application
./deploy.sh restart

# View debug logs
./deploy.sh logs
```

### Getting Help

```bash
# View deployment script help
./deploy.sh --help

# Check Docker documentation
docker --help

# Check Docker Compose documentation
docker-compose --help
```

## Advanced Usage

### Custom Nginx Configuration

Create custom nginx config:

```bash
# Edit nginx configuration
nano docker/nginx-custom.conf

# Mount custom config in docker-compose.yml
volumes:
  - ./docker/nginx-custom.conf:/etc/nginx/conf.d/custom.conf:ro
```

### Multi-Environment Deployment

Create environment-specific configs:

```bash
# Production
cp .env.example .env.production
./deploy.sh --env production deploy

# Staging
cp .env.example .env.staging
./deploy.sh --env staging deploy

# Development
cp .env.example .env.development
./deploy.sh --env development deploy
```

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and Deploy
        run: |
          chmod +x deploy.sh
          ./deploy.sh --force deploy
        env:
          VITE_API_URL: ${{ secrets.VITE_API_URL }}
          VITE_WS_URL: ${{ secrets.VITE_WS_URL }}
```

### Kubernetes Deployment

Convert Docker Compose to Kubernetes:

```bash
# Generate Kubernetes manifests
kompose convert -f docker-compose.yml

# Apply to cluster
kubectl apply -f .
```

### Backup and Restore

```bash
# Create backup
./deploy.sh backup

# Restore from backup
./deploy.sh restore ./backups/20240201_120000

# List backups
ls -la backups/
```

### Custom Scripts

Create custom deployment scripts:

```bash
#!/bin/bash
# custom-deploy.sh

# Custom deployment logic
./deploy.sh build
./deploy.sh deploy
./deploy.sh health

# Custom post-deployment checks
curl -f http://localhost:3000/health || exit 1

echo "Deployment successful!"
```

### Performance Tuning

#### Optimize for Production

```bash
# Set production optimizations
export NGINX_WORKER_PROCESSES=auto
export NGINX_WORKER_CONNECTIONS=2048
export NODE_ENV=production

# Enable gzip compression
# Configure cache headers
# Use CDN for static assets
```

#### Resource Limits

Configure in `docker-compose.yml`:

```yaml
services:
  frontend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Security Best Practices

1. **Use non-root user**: Already configured
2. **Regular updates**: Update base images regularly
3. **Scan for vulnerabilities**: Use `docker scan`
4. **Limit resources**: Set appropriate limits
5. **Secure secrets**: Use Docker secrets or vault
6. **Network segmentation**: Use custom networks
7. **SSL/TLS**: Use HTTPS in production
8. **Rate limiting**: Configure nginx rate limits

### Scaling

#### Horizontal Scaling

```bash
# Scale frontend instances
docker-compose up -d --scale frontend=5

# Use load balancer
docker-compose --profile loadbalancer up -d
```

#### Vertical Scaling

```bash
# Increase resource limits
# Edit docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

## Maintenance

### Regular Tasks

- **Daily**: Check logs and health
- **Weekly**: Update dependencies
- **Monthly**: Review resource usage
- **Quarterly**: Security audit

### Update Procedure

```bash
# 1. Backup current version
./deploy.sh backup

# 2. Pull latest changes
git pull

# 3. Build new version
./deploy.sh build

# 4. Deploy with rollback
./deploy.sh --rollback deploy

# 5. Verify deployment
./deploy.sh health

# 6. Monitor for issues
./deploy.sh logs -f
```

### Rollback Procedure

```bash
# Automatic rollback (if enabled)
./deploy.sh rollback

# Manual rollback
./deploy.sh restore ./backups/20240201_120000
```

## Support

For issues and questions:

1. Check this deployment guide
2. Review troubleshooting section
3. Check application logs: `./deploy.sh logs`
4. Review Docker logs: `docker logs <container>`
5. Open an issue in the repository

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
