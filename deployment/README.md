# Social Support Application System - Deployment Guide

This guide provides comprehensive instructions for deploying the Social Support Application Processing System across different environments and cloud platforms.

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Local Development with Docker Compose

1. **Clone and navigate to the project:**

   ```bash
   git clone <repository-url>
   cd social-support-system
   ```

2. **Set up environment variables:**

   ```bash
   cp deployment/config/.env.example deployment/config/.env.development
   # Edit the .env.development file with your settings
   ```

3. **Start the services:**

   ```bash
   cd deployment/docker
   docker-compose up -d
   ```

4. **Access the application:**
   - Main app: http://localhost:7860
   - Health check: http://localhost:7860/health

## Prerequisites

### Required Software

- **Docker** (20.10 or later)
- **Docker Compose** (2.0 or later)
- **Git**

### System Requirements

- **Memory**: Minimum 4GB RAM (8GB recommended for production)
- **Storage**: Minimum 20GB free space
- **CPU**: 2+ cores recommended

## Local Development

### Environment Setup

1. **Create environment file:**

   ```bash
   cp deployment/config/.env.example deployment/config/.env.development
   ```

2. **Configure environment variables:**

   ```bash
   # Edit deployment/config/.env.development
   DB_PASSWORD=your-secure-password
   SECRET_KEY=your-secret-key
   OLLAMA_HOST=ollama
   ```

3. **Start development environment:**
   ```bash
   cd deployment/docker
   docker-compose up -d
   ```

### Available Services

- **Application**: http://localhost:7860
- **Database**: PostgreSQL on port 5432
- **Redis**: Redis on port 6379
- **Ollama**: LLM service on port 11434
- **Nginx**: Reverse proxy on port 80

### Development Commands

```bash
# View logs
docker-compose logs -f app

# Restart a service
docker-compose restart app

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## Production Deployment

### 1. Build Production Image

```bash
# Build production image
./deployment/scripts/build.sh -e production -t v1.0.0

# Or with registry
./deployment/scripts/build.sh -e production -t v1.0.0 -r your-registry.com -p
```

### 2. Deploy with Docker Compose

```bash
# Set up production environment
cp deployment/config/.env.example deployment/config/.env.production
# Configure production values

# Deploy
cd deployment/docker
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Deploy using Universal Script

```bash
# Deploy to production
./deployment/scripts/deploy.sh -e production -p docker-compose -t v1.0.0
```

## Environment Configuration

### Environment Variables

| Variable      | Description            | Default        | Required |
| ------------- | ---------------------- | -------------- | -------- |
| `ENV`         | Environment name       | development    | No       |
| `DEBUG`       | Enable debug mode      | false          | No       |
| `SECRET_KEY`  | Application secret key | -              | Yes      |
| `DB_HOST`     | Database host          | localhost      | Yes      |
| `DB_PORT`     | Database port          | 5432           | Yes      |
| `DB_NAME`     | Database name          | social_support | Yes      |
| `DB_USER`     | Database username      | postgres       | Yes      |
| `DB_PASSWORD` | Database password      | -              | Yes      |
| `REDIS_HOST`  | Redis host             | localhost      | No       |
| `REDIS_PORT`  | Redis port             | 6379           | No       |
| `OLLAMA_HOST` | Ollama service host    | localhost      | Yes      |
| `OLLAMA_PORT` | Ollama service port    | 11434          | Yes      |

### Security Configuration

1. **Generate secure keys:**

   ```bash
   # Generate secret key
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # Generate database password
   openssl rand -base64 32
   ```

2. **Set proper file permissions:**
   ```bash
   chmod 600 deployment/config/.env.production
   ```

## Monitoring and Maintenance

### Health Checks

- **Application health**: `/health`
- **Database health**: Included in health endpoint
- **System resources**: CPU, memory, disk usage

### Monitoring with Prometheus and Grafana

1. **Enable monitoring:**

   ```bash
   # Production deployment includes monitoring
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Access monitoring:**
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000

### Log Management

```bash
# View application logs
docker-compose logs -f app

# View all logs
docker-compose logs -f

# Export logs
docker-compose logs --no-color > app-logs.txt
```

### Backup and Recovery

1. **Database backup:**

   ```bash
   ./deployment/scripts/backup-db.sh
   ```

2. **Restore database:**
   ```bash
   docker-compose exec db psql -U postgres -d social_support < backup.sql
   ```

## Troubleshooting

### Common Issues

1. **Database connection fails:**

   ```bash
   # Check database status
   docker-compose ps db

   # Check database logs
   docker-compose logs db

   # Restart database
   docker-compose restart db
   ```

2. **Ollama service not responding:**

   ```bash
   # Check Ollama status
   curl http://localhost:11434/api/health

   # Restart Ollama
   docker-compose restart ollama
   ```

3. **Application not accessible:**

   ```bash
   # Check application logs
   docker-compose logs app

   # Check port binding
   docker-compose ps

   # Test health endpoint
   curl http://localhost:7860/health
   ```

### Performance Issues

1. **High memory usage:**

   ```bash
   # Monitor resource usage
   docker stats

   # Adjust container memory limits in docker-compose.yml
   ```

2. **Slow response times:**

   ```bash
   # Check system resources
   python health_check.py

   # Scale application
   docker-compose up -d --scale app=2
   ```

### Log Analysis

```bash
# Search for errors
docker-compose logs app | grep -i error

# Monitor real-time logs
docker-compose logs -f app | grep -i -E "(error|warning|exception)"

# Check specific time range
docker-compose logs --since 1h app
```

## Security Best Practices

1. **Use secure passwords and keys**
2. **Keep images updated**
3. **Limit network exposure**
4. **Enable SSL/TLS in production**
5. **Regular security audits**
6. **Monitor access logs**

## Support and Maintenance

### Regular Maintenance Tasks

1. **Update dependencies:**

   ```bash
   # Update base images
   docker-compose pull

   # Rebuild with latest dependencies
   ./deployment/scripts/build.sh -e production
   ```

2. **Database maintenance:**

   ```bash
   # Backup database
   ./deployment/scripts/backup-db.sh

   # Optimize database
   docker-compose exec db psql -U postgres -d social_support -c "VACUUM ANALYZE;"
   ```

3. **Clean up unused resources:**

   ```bash
   # Remove unused images
   docker image prune

   # Remove unused volumes
   docker volume prune
   ```

## Contact and Support

For issues and support:

- Check the troubleshooting section above
- Review application logs
- Contact the development team

---

This deployment guide provides comprehensive instructions for deploying the Social Support Application Processing System across different environments. For additional help, refer to the individual cloud provider documentation and Docker best practices.
