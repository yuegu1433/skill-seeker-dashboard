#!/bin/bash
# ==============================================================================
# Docker Entrypoint Script for Skill Seekers Frontend
# Handles container initialization and environment setup
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Function to validate environment variables
validate_env() {
    log_info "Validating environment variables..."

    # Check for required API URLs
    if [ -z "$VITE_API_URL" ]; then
        log_warn "VITE_API_URL not set, using default: http://localhost:8000"
        export VITE_API_URL="http://localhost:8000"
    fi

    if [ -z "$VITE_WS_URL" ]; then
        log_warn "VITE_WS_URL not set, using default: ws://localhost:8000"
        export VITE_WS_URL="ws://localhost:8000"
    fi

    # Set default values if not provided
    export NGINX_WORKER_PROCESSES="${NGINX_WORKER_PROCESSES:-auto}"
    export NGINX_WORKER_CONNECTIONS="${NGINX_WORKER_CONNECTIONS:-1024}"
    export API_HOST="${API_HOST:-backend:8000}"
    export WS_HOST="${WS_HOST:-backend:8000}"
    export HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30}"

    log_info "Environment validation completed"
}

# Function to setup nginx configuration
setup_nginx() {
    log_info "Setting up Nginx configuration..."

    # Update nginx.conf with environment variables
    if [ -f /etc/nginx/nginx.conf ]; then
        envsubst '${API_HOST} ${WS_HOST}' < /etc/nginx/nginx.conf > /tmp/nginx.conf
        mv /tmp/nginx.conf /etc/nginx/nginx.conf
        log_info "Updated nginx.conf with environment variables"
    fi

    # Update default.conf with environment variables
    if [ -f /etc/nginx/conf.d/default.conf ]; then
        envsubst '${API_HOST} ${WS_HOST}' < /etc/nginx/conf.d/default.conf > /tmp/default.conf
        mv /tmp/default.conf /etc/nginx/conf.d/default.conf
        log_info "Updated default.conf with environment variables"
    fi

    # Set nginx worker settings
    export worker_processes="$NGINX_WORKER_PROCESSES"
    export worker_connections="$NGINX_WORKER_CONNECTIONS"

    log_info "Nginx configuration setup completed"
}

# Function to create necessary directories
setup_directories() {
    log_info "Creating necessary directories..."

    # Create log directory if it doesn't exist
    if [ ! -d "/var/log/nginx" ]; then
        mkdir -p /var/log/nginx
        chown nginx-app:nginx-app /var/log/nginx
    fi

    # Create cache directories
    for dir in /var/cache/nginx/client_temp \
               /var/cache/nginx/proxy_temp \
               /var/cache/nginx/fastcgi_temp \
               /var/cache/nginx/uwsgi_temp \
               /var/cache/nginx/scgi_temp; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            chown nginx-app:nginx-app "$dir"
        fi
    done

    log_info "Directories setup completed"
}

# Function to check if required files exist
check_files() {
    log_info "Checking required files..."

    # Check if index.html exists
    if [ ! -f "/usr/share/nginx/html/index.html" ]; then
        log_error "index.html not found in /usr/share/nginx/html/"
        log_error "Make sure the application was built correctly"
        exit 1
    fi

    # Check if nginx.conf exists
    if [ ! -f "/etc/nginx/nginx.conf" ]; then
        log_error "nginx.conf not found"
        exit 1
    fi

    # Check if default.conf exists
    if [ ! -f "/etc/nginx/conf.d/default.conf" ]; then
        log_error "default.conf not found"
        exit 1
    fi

    log_info "All required files found"
}

# Function to test nginx configuration
test_nginx_config() {
    log_info "Testing Nginx configuration..."

    if nginx -t; then
        log_info "Nginx configuration is valid"
        return 0
    else
        log_error "Nginx configuration test failed"
        return 1
    fi
}

# Function to display container information
display_info() {
    log_info "============================================"
    log_info "Skill Seekers Frontend Container Started"
    log_info "============================================"
    log_info "Version: $VITE_APP_VERSION"
    log_info "API URL: $VITE_API_URL"
    log_info "WebSocket URL: $VITE_WS_URL"
    log_info "Node Environment: $NODE_ENV"
    log_info "============================================"
}

# Function to setup signal handlers
setup_signals() {
    log_info "Setting up signal handlers..."

    # Trap SIGTERM and SIGINT for graceful shutdown
    trap 'log_info "Received SIGTERM/SIGINT, shutting down..."; nginx -s quit; exit 0' TERM INT

    # Trap SIGHUP for config reload
    trap 'log_info "Received SIGHUP, reloading configuration..."; nginx -s reload' HUP

    # Trap SIGUSR1 for log rotation
    trap 'log_info "Received SIGUSR1, reopening log files..."; nginx -s reopen' USR1
}

# Main execution
main() {
    log_info "Starting container initialization..."

    # Validate environment
    validate_env

    # Setup directories
    setup_directories

    # Setup nginx configuration
    setup_nginx

    # Check required files
    check_files

    # Test nginx configuration
    if ! test_nginx_config; then
        log_error "Nginx configuration test failed, exiting..."
        exit 1
    fi

    # Setup signal handlers
    setup_signals

    # Display container information
    display_info

    log_info "Container initialization completed successfully"
    log_info "Starting Nginx..."

    # Start nginx in foreground mode
    exec "$@"
}

# Run main function with all arguments
main "$@"
