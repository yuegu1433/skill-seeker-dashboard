# Docker Configuration Guide

This directory contains Docker-related configuration files for the Skill Seekers Frontend application.

## Directory Structure

```
docker/
├── README.md                    # This file
├── entrypoint.sh               # Container initialization script
├── healthcheck.sh              # Health check script
├── prometheus.yml              # Prometheus monitoring config
├── haproxy.cfg                # HAProxy load balancer config
├── grafana/
│   ├── datasources/
│   │   └── prometheus.yml     # Grafana data sources
│   └── dashboards/
│       └── dashboard.yml       # Grafana dashboard config
└── nginx-proxy.conf            # Nginx reverse proxy config (optional)
```

## Scripts

### entrypoint.sh

Container initialization script that:
- Validates environment variables
- Sets up Nginx configuration
- Creates necessary directories
- Checks required files
- Tests Nginx configuration
- Sets up signal handlers
- Starts Nginx

Usage: Automatically runs when container starts

### healthcheck.sh

Health check script that validates:
- Nginx process status
- Port listening
- HTTP health endpoint
- Index file accessibility
- Configuration validity
- Disk space
- Memory usage

Usage:
```bash
# Full health check
./healthcheck.sh full

# Quick health check
./healthcheck.sh quick

# Docker health check
docker exec <container> /usr/local/bin/healthcheck.sh
```

## Configuration Files

### prometheus.yml

Prometheus configuration for monitoring:
- Scrape intervals
- Target endpoints
- Alert rules
- Metrics collection

### haproxy.cfg

HAProxy load balancer configuration:
- Frontend rules
- Backend servers
- Health checks
- SSL termination
- Stats page

### grafana/

Grafana configuration for visualization:
- Data sources (Prometheus)
- Dashboard provisioning
- Panel configurations

## Usage Examples

### Running Health Check

```bash
# Inside container
docker exec skillseekers-frontend /usr/local/bin/healthcheck.sh

# From host
./docker/healthcheck.sh quick
```

### Monitoring Setup

```bash
# Start with monitoring
docker-compose --profile monitoring up -d

# Access Grafana
# http://localhost:3001
# Default credentials: admin/admin

# Access Prometheus
# http://localhost:9090
```

### Load Balancer Setup

```bash
# Start with load balancer
docker-compose --profile loadbalancer up -d

# Access load balancer stats
# http://localhost:8404/stats
```

## Customization

### Custom Nginx Configuration

1. Edit `nginx.conf` or `nginx-default.conf`
2. Rebuild image: `./deploy.sh build`
3. Restart: `./deploy.sh restart`

### Custom Health Checks

Modify `healthcheck.sh` to add custom checks:

```bash
# Add custom check
check_custom_feature() {
    # Your validation logic
    return 0  # Success
}

# Add to perform_health_check()
log_info "Check 8/8: Testing custom feature..."
if check_custom_feature; then
    log_info "✓ Custom feature check passed"
    checks_passed=$((checks_passed + 1))
else
    log_error "✗ Custom feature check failed"
fi
```

### Custom Monitoring

Add custom metrics to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'custom-metrics'
    static_configs:
      - targets: ['your-service:port']
    metrics_path: '/custom/metrics'
    scrape_interval: 30s
```

## Troubleshooting

### Health Check Failures

```bash
# Debug health check
docker exec skillseekers-frontend /usr/local/bin/healthcheck.sh full

# Check nginx logs
docker logs skillseekers-frontend

# Test nginx config
docker exec skillseekers-frontend nginx -t
```

### Monitoring Issues

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana logs
docker logs skillseekers-grafana

# Verify Prometheus config
docker exec skillseekers-prometheus cat /etc/prometheus/prometheus.yml
```

### Load Balancer Issues

```bash
# Check HAProxy stats
curl http://localhost:8404/stats

# Test backend servers
curl http://localhost:80/health

# Check HAProxy logs
docker logs skillseekers-haproxy
```

## Security

### Best Practices

1. **Non-root user**: Containers run as non-root user
2. **Minimal images**: Alpine Linux base
3. **No build tools in runtime**: Multi-stage builds
4. **Read-only filesystems**: Where possible
5. **Resource limits**: CPU and memory limits
6. **Security headers**: Configured in Nginx

### SSL/TLS

For HTTPS deployment:

1. Obtain SSL certificates
2. Place in `/etc/nginx/ssl/`
3. Uncomment SSL server block in configuration
4. Update `docker-compose.yml` to mount certificates

Example:
```yaml
volumes:
  - ./ssl:/etc/nginx/ssl:ro
```

## Performance

### Optimization Tips

1. **Enable compression**: Gzip/Brotli
2. **Configure caching**: Static assets
3. **Use CDN**: For global deployment
4. **Resource limits**: Prevent resource exhaustion
5. **Health checks**: Monitor container health

### Monitoring Metrics

Key metrics to monitor:
- Response time
- Throughput
- Error rate
- CPU usage
- Memory usage
- Disk I/O
- Network I/O

## Maintenance

### Regular Tasks

1. **Update base images**: Monthly
2. **Review logs**: Weekly
3. **Check health**: Daily
4. **Monitor metrics**: Continuous
5. **Update certificates**: Before expiration

### Backup

Configuration backup:
```bash
# Backup Docker configs
tar -czf docker-config-backup.tar.gz docker/

# Backup environment
cp .env .env.backup
```

## Support

For issues with Docker configuration:

1. Check this guide
2. Review logs: `docker logs <container>`
3. Test configuration: `docker exec <container> nginx -t`
4. Check health: `./docker/healthcheck.sh`
5. Open an issue in the repository

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [HAProxy Documentation](http://www.haproxy.org/)
