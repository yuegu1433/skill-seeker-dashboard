#!/bin/sh
# ==============================================================================
# Health Check Script for Skill Seekers Frontend
# Checks if the application is healthy and responding correctly
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
HEALTH_CHECK_PORT=${HEALTH_CHECK_PORT:-80}
HEALTH_CHECK_PATH=${HEALTH_CHECK_PATH:-/health}
HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL:-30}
TIMEOUT=${TIMEOUT:-5}
MAX_RETRIES=${MAX_RETRIES:-3}
RETRY_DELAY=${RETRY_DELAY:-2}

# Logging functions
log_info() {
    echo -e "${GREEN}[HEALTHCHECK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[HEALTHCHECK]${NC} $1"
}

log_error() {
    echo -e "${RED}[HEALTHCHECK]${NC} $1"
}

# Function to check if nginx process is running
check_nginx_process() {
    if pgrep -x nginx > /dev/null; then
        return 0
    else
        log_error "Nginx process is not running"
        return 1
    fi
}

# Function to check HTTP health endpoint
check_http_health() {
    local url="http://localhost:${HEALTH_CHECK_PORT}${HEALTH_CHECK_PATH}"
    local response

    # Try to get HTTP response
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time "${TIMEOUT}" \
        --connect-timeout "${TIMEOUT}" \
        "$url" 2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        return 0
    else
        log_error "Health endpoint returned HTTP $response"
        return 1
    fi
}

# Function to check if index.html exists and is readable
check_index_file() {
    if [ -f "/usr/share/nginx/html/index.html" ] && [ -r "/usr/share/nginx/html/index.html" ]; then
        return 0
    else
        log_error "index.html not found or not readable"
        return 1
    fi
}

# Function to check if configuration files are valid
check_config_files() {
    if nginx -t > /dev/null 2>&1; then
        return 0
    else
        log_error "Nginx configuration is invalid"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    # Check if disk space is less than 90%
    local disk_usage
    disk_usage=$(df /usr/share/nginx/html | awk 'NR==2 {print $5}' | sed 's/%//')

    if [ "$disk_usage" -lt 90 ]; then
        return 0
    else
        log_error "Disk space is low: ${disk_usage}%"
        return 1
    fi
}

# Function to check memory usage
check_memory() {
    # Check if memory usage is less than 90%
    local mem_usage
    mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')

    if [ "$mem_usage" -lt 90 ]; then
        return 0
    else
        log_warn "Memory usage is high: ${mem_usage}%"
        # Don't fail on high memory, just warn
        return 0
    fi
}

# Function to check if port is listening
check_port_listening() {
    if netstat -tuln 2>/dev/null | grep -q ":${HEALTH_CHECK_PORT} "; then
        return 0
    else
        log_error "Port ${HEALTH_CHECK_PORT} is not listening"
        return 1
    fi
}

# Function to perform comprehensive health check
perform_health_check() {
    log_info "Starting health check..."

    local checks_passed=0
    local checks_total=0

    # Check 1: Nginx process
    checks_total=$((checks_total + 1))
    log_info "Check 1/7: Testing nginx process..."
    if check_nginx_process; then
        log_info "✓ Nginx process is running"
        checks_passed=$((checks_passed + 1))
    else
        log_error "✗ Nginx process check failed"
    fi

    # Check 2: Port listening
    checks_total=$((checks_total + 1))
    log_info "Check 2/7: Testing port listening..."
    if check_port_listening; then
        log_info "✓ Port ${HEALTH_CHECK_PORT} is listening"
        checks_passed=$((checks_passed + 1))
    else
        log_error "✗ Port listening check failed"
    fi

    # Check 3: HTTP health endpoint
    checks_total=$((checks_total + 1))
    log_info "Check 3/7: Testing HTTP health endpoint..."
    if check_http_health; then
        log_info "✓ HTTP health endpoint is responding"
        checks_passed=$((checks_passed + 1))
    else
        log_error "✗ HTTP health endpoint check failed"
    fi

    # Check 4: Index file
    checks_total=$((checks_total + 1))
    log_info "Check 4/7: Testing index.html..."
    if check_index_file; then
        log_info "✓ index.html exists and is readable"
        checks_passed=$((checks_passed + 1))
    else
        log_error "✗ Index file check failed"
    fi

    # Check 5: Configuration files
    checks_total=$((checks_total + 1))
    log_info "Check 5/7: Testing nginx configuration..."
    if check_config_files; then
        log_info "✓ Nginx configuration is valid"
        checks_passed=$((checks_passed + 1))
    else
        log_error "✗ Configuration check failed"
    fi

    # Check 6: Disk space
    checks_total=$((checks_total + 1))
    log_info "Check 6/7: Testing disk space..."
    if check_disk_space; then
        log_info "✓ Disk space is sufficient"
        checks_passed=$((checks_passed + 1))
    else
        log_error "✗ Disk space check failed"
    fi

    # Check 7: Memory usage
    checks_total=$((checks_total + 1))
    log_info "Check 7/7: Testing memory usage..."
    if check_memory; then
        log_info "✓ Memory usage is acceptable"
        checks_passed=$((checks_passed + 1))
    else
        log_warn "✗ Memory usage check had issues"
        checks_passed=$((checks_passed + 1)) # Don't fail on memory warning
    fi

    # Summary
    log_info "========================================"
    log_info "Health Check Summary"
    log_info "========================================"
    log_info "Checks Passed: $checks_passed/$checks_total"

    if [ $checks_passed -eq $checks_total ]; then
        log_info "✓ All health checks passed"
        return 0
    else
        log_error "✗ Some health checks failed"
        return 1
    fi
}

# Function to perform quick health check (for Kubernetes)
quick_health_check() {
    # Quick check: just test the HTTP endpoint
    if check_http_health; then
        return 0
    else
        return 1
    fi
}

# Main function
main() {
    local check_type="${1:-full}"

    case "$check_type" in
        "quick")
            log_info "Performing quick health check..."
            if quick_health_check; then
                log_info "Quick health check passed"
                exit 0
            else
                log_error "Quick health check failed"
                exit 1
            fi
            ;;
        "full")
            if perform_health_check; then
                exit 0
            else
                exit 1
            fi
            ;;
        *)
            log_error "Unknown check type: $check_type"
            log_info "Usage: $0 [quick|full]"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
