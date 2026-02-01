#!/bin/bash
# ==============================================================================
# Skill Seekers Frontend - Deployment Script
# Automated deployment with health checks and rollback support
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="skillseekers-frontend"
IMAGE_NAME="$PROJECT_NAME:latest"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
ENV_FILE="$SCRIPT_DIR/.env"

# Default values
ENVIRONMENT="development"
ACTION=""
BACKUP_RETENTION=7
HEALTH_CHECK_TIMEOUT=120
HEALTH_CHECK_INTERVAL=10
ROLLBACK_TIMEOUT=60

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to display usage
usage() {
    cat << EOF
Skill Seekers Frontend - Deployment Script

Usage: $0 [OPTIONS] ACTION

OPTIONS:
    -h, --help          Show this help message
    -e, --env           Set environment (development|production|staging)
    -f, --force         Force deployment without confirmation
    -t, --timeout       Set health check timeout (seconds)
    --rollback          Enable rollback support
    --no-cache          Build without cache
    --parallel          Build in parallel

ACTIONS:
    build               Build the Docker image
    deploy              Build and deploy the application
    start               Start the application
    stop                Stop the application
    restart             Restart the application
    status              Show application status
    logs                Show application logs
    health              Run health check
    cleanup             Clean up containers and images
    rollback            Rollback to previous version
    backup              Create backup
    restore             Restore from backup

EXAMPLES:
    $0 --env production deploy
    $0 --force --no-cache build
    $0 --rollback rollback
    $0 health

EOF
    exit 0
}

# Function to check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check if docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi

    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_warn "Environment file not found: $ENV_FILE"
        log_info "Creating default .env file..."
        create_default_env
    fi

    log_info "Prerequisites check completed"
}

# Function to create default environment file
create_default_env() {
    cat > "$ENV_FILE" << EOF
# ==============================================================================
# Skill Seekers Frontend - Environment Configuration
# ==============================================================================

# Application
VITE_APP_VERSION=1.0.0
NODE_ENV=production

# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
API_HOST=backend:8000
WS_HOST=backend:8000

# Ports
FRONTEND_PORT=3000
FRONTEND_DEV_PORT=3001
NGINX_PORT=80
NGINX_SSL_PORT=443
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
REDIS_PORT=6379

# Nginx Configuration
NGINX_WORKER_PROCESSES=auto
NGINX_WORKER_CONNECTIONS=1024
HEALTH_CHECK_INTERVAL=30

# Database (Optional)
POSTGRES_DB=skillseekers
POSTGRES_USER=user
POSTGRES_PASSWORD=changeme
DATABASE_URL=postgresql://user:changeme@db:5432/skillseekers
REDIS_URL=redis://redis:6379

# MinIO (Optional)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=http://minio:9000
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# Monitoring (Optional)
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

# Load Balancer (Optional)
LOADBALANCER_PORT=8080

# Backup Configuration
BACKUP_RETENTION=7
EOF

    log_info "Default environment file created: $ENV_FILE"
}

# Function to load environment variables
load_env() {
    log_step "Loading environment variables..."

    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
        log_info "Environment variables loaded from $ENV_FILE"
    fi

    # Override with command line arguments
    export NODE_ENV="$ENVIRONMENT"
    log_info "Environment set to: $ENVIRONMENT"
}

# Function to build the Docker image
build_image() {
    log_step "Building Docker image..."

    local build_args=""
    if [ "$NO_CACHE" = "true" ]; then
        build_args="--no-cache"
        log_info "Building without cache"
    fi

    if [ "$PARALLEL" = "true" ]; then
        build_args="$build_args --parallel"
        log_info "Building in parallel"
    fi

    # Build arguments
    local build_cmd="docker build $build_args -t $IMAGE_NAME ."
    build_cmd="$build_cmd --build-arg NODE_ENV=$ENVIRONMENT"
    build_cmd="$build_cmd --build-arg VITE_API_URL=${VITE_API_URL}"
    build_cmd="$build_cmd --build-arg VITE_WS_URL=${VITE_WS_URL}"
    build_cmd="$build_cmd --build-arg VITE_APP_VERSION=${VITE_APP_VERSION}"

    log_info "Running: $build_cmd"
    eval "$build_cmd"

    if [ $? -eq 0 ]; then
        log_info "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Function to start the application
start_application() {
    log_step "Starting application..."

    # Select compose file based on environment
    local compose_file="$COMPOSE_FILE"
    if [ "$ENVIRONMENT" = "development" ]; then
        compose_file="$compose_file"
    fi

    # Start services
    docker-compose -f "$compose_file" -p "$PROJECT_NAME" up -d

    if [ $? -eq 0 ]; then
        log_info "Application started successfully"
    else
        log_error "Failed to start application"
        exit 1
    fi
}

# Function to stop the application
stop_application() {
    log_step "Stopping application..."

    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down

    if [ $? -eq 0 ]; then
        log_info "Application stopped successfully"
    else
        log_error "Failed to stop application"
        exit 1
    fi
}

# Function to restart the application
restart_application() {
    log_step "Restarting application..."

    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" restart

    if [ $? -eq 0 ]; then
        log_info "Application restarted successfully"
    else
        log_error "Failed to restart application"
        exit 1
    fi
}

# Function to show application status
show_status() {
    log_step "Application status..."

    echo ""
    echo "=== Docker Containers ==="
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps

    echo ""
    echo "=== Docker Images ==="
    docker images | grep "$PROJECT_NAME" || echo "No images found"

    echo ""
    echo "=== Resource Usage ==="
    docker stats --no-stream $(docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps -q) 2>/dev/null || echo "No running containers"
}

# Function to show logs
show_logs() {
    log_step "Application logs..."

    local service="${1:-frontend}"
    local lines="${2:-100}"

    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs --tail="$lines" -f "$service"
}

# Function to run health check
run_health_check() {
    log_step "Running health check..."

    local timeout="$HEALTH_CHECK_TIMEOUT"
    local interval="$HEALTH_CHECK_INTERVAL"
    local container_name="$PROJECT_NAME-frontend-1"

    # Wait for container to be running
    log_info "Waiting for container to start..."
    local count=0
    while [ $count -lt $((timeout / interval)) ]; do
        if docker ps | grep -q "$container_name"; then
            break
        fi
        sleep "$interval"
        count=$((count + 1))
    done

    if ! docker ps | grep -q "$container_name"; then
        log_error "Container did not start within timeout"
        return 1
    fi

    # Run health check inside container
    log_info "Running health checks..."
    docker exec "$container_name" /usr/local/bin/healthcheck.sh full

    if [ $? -eq 0 ]; then
        log_info "Health check passed ✓"
        return 0
    else
        log_error "Health check failed ✗"
        return 1
    fi
}

# Function to deploy the application
deploy_application() {
    log_step "Deploying application..."

    # Build image
    build_image

    # Stop existing application
    log_info "Stopping existing application..."
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down || true

    # Create backup if needed
    if [ "$ROLLBACK" = "true" ]; then
        backup_application
    fi

    # Start application
    start_application

    # Wait for health check
    log_info "Waiting for application to be healthy..."
    sleep 30

    if run_health_check; then
        log_info "Deployment completed successfully ✓"
    else
        log_error "Deployment failed - Health check failed"
        if [ "$ROLLBACK" = "true" ]; then
            log_warn "Rolling back to previous version..."
            rollback_application
        fi
        exit 1
    fi
}

# Function to backup application
backup_application() {
    log_step "Creating backup..."

    local backup_dir="$SCRIPT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup environment file
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$backup_dir/"
    fi

    # Backup Docker Compose file
    cp "$COMPOSE_FILE" "$backup_dir/"

    # Save Docker images
    docker save "$IMAGE_NAME" | gzip > "$backup_dir/image.tar.gz"

    log_info "Backup created: $backup_dir"

    # Cleanup old backups
    cleanup_old_backups
}

# Function to restore from backup
restore_application() {
    log_step "Restoring from backup..."

    local backup_dir="$1"
    if [ -z "$backup_dir" ]; then
        log_error "Backup directory not specified"
        exit 1
    fi

    if [ ! -d "$backup_dir" ]; then
        log_error "Backup directory not found: $backup_dir"
        exit 1
    fi

    # Stop application
    stop_application

    # Restore environment file
    if [ -f "$backup_dir/.env" ]; then
        cp "$backup_dir/.env" "$ENV_FILE"
        log_info "Environment file restored"
    fi

    # Load Docker image
    if [ -f "$backup_dir/image.tar.gz" ]; then
        gunzip -c "$backup_dir/image.tar.gz" | docker load
        log_info "Docker image restored"
    fi

    # Start application
    start_application

    log_info "Restore completed"
}

# Function to rollback to previous version
rollback_application() {
    log_step "Rolling back to previous version..."

    # Find latest backup
    local backup_dir=$(ls -td "$SCRIPT_DIR/backups"/*/ 2>/dev/null | head -n 1)

    if [ -z "$backup_dir" ]; then
        log_error "No backup found for rollback"
        exit 1
    fi

    log_info "Rolling back to: $backup_dir"
    restore_application "$backup_dir"

    log_info "Rollback completed"
}

# Function to cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (retention: $BACKUP_RETENTION days)..."

    find "$SCRIPT_DIR/backups" -type d -mtime +$BACKUP_RETENTION -exec rm -rf {} + 2>/dev/null || true

    log_info "Cleanup completed"
}

# Function to cleanup containers and images
cleanup() {
    log_step "Cleaning up containers and images..."

    # Stop and remove containers
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down -v

    # Remove unused images
    docker image prune -f

    # Remove unused volumes
    docker volume prune -f

    # Remove unused networks
    docker network prune -f

    log_info "Cleanup completed"
}

# Function to confirm action
confirm_action() {
    if [ "$FORCE" = "true" ]; then
        return 0
    fi

    local action="$1"
    echo ""
    log_warn "You are about to: $action"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Action cancelled"
        exit 0
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--force)
            FORCE="true"
            shift
            ;;
        -t|--timeout)
            HEALTH_CHECK_TIMEOUT="$2"
            shift 2
            ;;
        --rollback)
            ROLLBACK="true"
            shift
            ;;
        --no-cache)
            NO_CACHE="true"
            shift
            ;;
        --parallel)
            PARALLEL="true"
            shift
            ;;
        build)
            ACTION="build"
            shift
            ;;
        deploy)
            ACTION="deploy"
            shift
            ;;
        start)
            ACTION="start"
            shift
            ;;
        stop)
            ACTION="stop"
            shift
            ;;
        restart)
            ACTION="restart"
            shift
            ;;
        status)
            ACTION="status"
            shift
            ;;
        logs)
            ACTION="logs"
            shift
            ;;
        health)
            ACTION="health"
            shift
            ;;
        cleanup)
            ACTION="cleanup"
            shift
            ;;
        rollback)
            ACTION="rollback"
            shift
            ;;
        backup)
            ACTION="backup"
            shift
            ;;
        restore)
            ACTION="restore"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Main execution
main() {
    echo ""
    log_info "============================================"
    log_info "Skill Seekers Frontend - Deployment Script"
    log_info "============================================"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Load environment
    load_env

    # Execute action
    case "$ACTION" in
        build)
            confirm_action "build the Docker image"
            build_image
            ;;
        deploy)
            confirm_action "deploy the application"
            deploy_application
            ;;
        start)
            confirm_action "start the application"
            start_application
            ;;
        stop)
            confirm_action "stop the application"
            confirm_action "stop the application"
            stop_application
            ;;
        restart)
            confirm_action "restart the application"
            restart_application
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$@"
            ;;
        health)
            run_health_check
            ;;
        cleanup)
            confirm_action "cleanup containers and images"
            cleanup
            ;;
        rollback)
            confirm_action "rollback to previous version"
            rollback_application
            ;;
        backup)
            backup_application
            ;;
        restore)
            restore_application "$2"
            ;;
        *)
            log_error "No action specified"
            usage
            ;;
    esac

    echo ""
    log_info "============================================"
    log_info "Completed successfully"
    log_info "============================================"
    echo ""
}

# Run main function
main "$@"
