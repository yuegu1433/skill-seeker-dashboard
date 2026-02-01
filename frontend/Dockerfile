# ==============================================================================
# Skill Seekers Frontend - Production Dockerfile
# Multi-stage build for optimized production deployment
# ==============================================================================

# Stage 1: Dependencies Installation
# Use official Node.js LTS image
FROM node:18-alpine AS deps

# Set working directory
WORKDIR /app

# Add metadata
LABEL maintainer="Skill Seekers Team"
LABEL description="Skill Seekers Frontend - Dependencies"
LABEL version="1.0.0"

# Install system dependencies for native modules
RUN apk add --no-cache \
    libc6-compat \
    python3 \
    make \
    g++ \
    cairo-dev \
    jpeg-dev \
    pango-dev \
    musl-dev \
    giflib-dev \
    pixman-dev \
    pangomm-dev \
    libjpeg-turbo-dev \
    freetype-dev

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
# Use npm ci for faster, more reliable builds
RUN npm ci --only=production --ignore-scripts

# ==============================================================================
# Stage 2: Build Application
# ==============================================================================
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Add metadata
LABEL maintainer="Skill Seekers Team"
LABEL description="Skill Seekers Frontend - Build"
LABEL version="1.0.0"

# Copy dependency files from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Add build arguments for environment configuration
ARG NODE_ENV=production
ARG VITE_API_URL
ARG VITE_WS_URL
ARG VITE_APP_VERSION

# Set environment variables
ENV NODE_ENV=${NODE_ENV}
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_WS_URL=${VITE_WS_URL}
ENV VITE_APP_VERSION=${VITE_APP_VERSION}

# Install all dependencies (including dev dependencies for building)
RUN npm ci

# Build the application
# Enable minification, source maps disabled for production
RUN npm run build

# ==============================================================================
# Stage 3: Production Runtime
# ==============================================================================
# Use Alpine Linux with Nginx for optimal performance
FROM nginx:alpine AS runner

# Install security updates and additional utilities
RUN apk add --no-cache \
    curl \
    jq \
    bash \
    gettext \
    tzdata \
    && rm -rf /var/cache/apk/*

# Add metadata
LABEL maintainer="Skill Seekers Team"
LABEL description="Skill Seekers Frontend - Production Runtime"
LABEL version="1.0.0"

# Create non-root user for security
RUN addgroup -g 1001 -S nginx-app && \
    adduser -S nginx-app -u 1001 -G nginx-app

# Set working directory
WORKDIR /usr/share/nginx/html

# Remove default nginx files
RUN rm -rf /usr/share/nginx/html/*

# Copy built application from builder stage
COPY --from=builder --chown=nginx-app:nginx-app /app/dist .

# Copy production nginx configuration
COPY --chown=nginx-app:nginx-app nginx.conf /etc/nginx/nginx.conf
COPY --chown=nginx-app:nginx-app nginx-default.conf /etc/nginx/conf.d/default.conf

# Copy health check script
COPY --chown=nginx-app:nginx-app docker/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# Create directories for logs and temporary files
RUN mkdir -p /var/log/nginx && \
    mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/cache/nginx/proxy_temp && \
    mkdir -p /var/cache/nginx/fastcgi_temp && \
    mkdir -p /var/cache/nginx/uwsgi_temp && \
    mkdir -p /var/cache/nginx/scgi_temp && \
    chown -R nginx-app:nginx-app /var/log/nginx && \
    chown -R nginx-app:nginx-app /var/cache/nginx

# Copy entrypoint script for container initialization
COPY --chown=nginx-app:nginx-app docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose port 80 (HTTP)
EXPOSE 80

# Add labels for better Docker experience
LABEL frontend.component="SkillSeekers"
LABEL frontend.component.type="web-server"
LABEL frontend.architecture="nginx"

# Switch to non-root user
USER nginx-app

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# ==============================================================================
# Stage 4: Development Runtime (Optional)
# ==============================================================================
# This stage is for development purposes only
FROM node:18-alpine AS development

# Set working directory
WORKDIR /app

# Add metadata
LABEL maintainer="Skill Seekers Team"
LABEL description="Skill Seekers Frontend - Development"
LABEL version="1.0.0"

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

# Expose development server port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ==============================================================================
# Build Arguments and Environment Variables
# ==============================================================================
# Build-time arguments:
# --build-arg NODE_ENV=production
# --build-arg VITE_API_URL=http://api.example.com
# --build-arg VITE_WS_URL=ws://api.example.com
# --build-arg VITE_APP_VERSION=1.0.0

# Runtime environment variables (can be set when running container):
# - NODE_ENV=production
# - NGINX_WORKER_PROCESSES=auto
# - NGINX_WORKER_CONNECTIONS=1024
# - API_PROXY_PASS=http://backend:8000
# - HEALTH_CHECK_INTERVAL=30

# ==============================================================================
# Multi-stage Build Notes
# ==============================================================================
# 1. deps: Installs only production dependencies
# 2. builder: Builds the application with all optimizations
# 3. runner: Production-ready nginx server with security hardening
# 4. development: Optional stage for local development

# To build production image:
# docker build -t skillseekers-frontend:latest .
# docker build --target runner -t skillseekers-frontend:latest .

# To build development image:
# docker build --target development -t skillseekers-frontend:dev .

# ==============================================================================
# Security Notes
# ==============================================================================
# 1. Non-root user (nginx-app) runs the application
# 2. Minimal Alpine Linux base image reduces attack surface
# 3. No build tools or source code in final runtime image
# 4. Security-focused nginx configuration
# 5. Regular security updates via apk
# ==============================================================================
