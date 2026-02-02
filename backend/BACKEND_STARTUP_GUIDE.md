# 后端服务启动指南

## 概述

本指南详细说明如何启动技能管理系统的后端服务，包括开发环境、生产环境和Docker启动方式。

## 目录结构

```
backend/
├── app/                          # 应用代码
│   ├── __init__.py
│   ├── main.py                   # FastAPI应用入口
│   ├── api/                      # API路由
│   ├── core/                     # 核心配置
│   ├── db/                       # 数据库
│   ├── models/                   # 数据模型
│   ├── schemas/                  # Pydantic模型
│   └── services/                 # 业务逻辑
├── tests/                        # 测试文件
├── alembic/                      # 数据库迁移
├── alembic.ini                   # Alembic配置
├── requirements.txt              # Python依赖
├── .env.example                  # 环境变量模板
├── docker-compose.yml           # Docker编排
├── Dockerfile                    # Docker镜像
└── Makefile                     # 构建脚本
```

## 1. 环境准备

### 系统要求

- **Python**: 3.9+
- **PostgreSQL**: 12+
- **Redis**: 6+
- **MinIO**: 2023+
- **Docker**: 20.10+ (可选)

### 安装依赖

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 2. 环境配置

### 2.1 复制环境变量

```bash
cp .env.example .env
```

### 2.2 配置.env文件

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/skillseekers
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=skillseekers
DATABASE_USER=user
DATABASE_PASSWORD=password

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=skill-files

# API配置
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
DEBUG=True

# 安全配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### 2.3 创建日志目录

```bash
mkdir -p logs
```

## 3. 数据库设置

### 3.1 创建数据库

```bash
# 连接PostgreSQL
psql -U postgres

# 创建数据库和用户
CREATE DATABASE skillseekers;
CREATE USER skilluser WITH PASSWORD 'skillpass';
GRANT ALL PRIVILEGES ON DATABASE skillseekers TO skilluser;
\q
```

### 3.2 运行数据库迁移

```bash
# 初始化Alembic
alembic init alembic

# 生成迁移文件
alembic revision --autogenerate -m "Initial migration"

# 应用迁移
alembic upgrade head
```

## 4. 服务启动

### 4.1 开发模式启动 (推荐)

#### 启动方式一：直接启动

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 启动方式二：使用脚本

```bash
# 使用启动脚本
python start_dev.py

# 或使用make命令
make dev
```

#### 启动方式三：使用Docker Compose

```bash
# 启动开发环境 (包含数据库、Redis、MinIO)
docker-compose -f docker-compose.dev.yml up -d

# 进入容器启动服务
docker exec -it skillseekers-backend bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.2 生产模式启动

#### 启动方式一：直接启动

```bash
# 激活虚拟环境
source venv/bin/activate

# 使用Gunicorn启动
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 启动方式二：使用Docker

```bash
# 构建镜像
docker build -t skillseekers-backend .

# 启动容器
docker run -d \
  --name skillseekers-backend \
  -p 8000:8000 \
  --env-file .env \
  skillseekers-backend
```

#### 启动方式三：使用Docker Compose

```bash
# 启动生产环境
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### 4.3 后台服务启动

#### 使用Screen (Linux/Mac)

```bash
# 安装screen
apt-get install screen  # Ubuntu/Debian
yum install screen     # CentOS/RHEL

# 创建screen会话
screen -S backend

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 分离会话 (Ctrl+A, D)

# 重新连接会话
screen -r backend
```

#### 使用PM2 (Node.js工具)

```bash
# 安装PM2
npm install -g pm2

# 创建ecosystem文件
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'skillseekers-backend',
    script: 'uvicorn',
    args: 'app.main:app --host 0.0.0.0 --port 8000',
    cwd: '/path/to/backend',
    interpreter: '/path/to/venv/bin/python',
    env: {
      PYTHONPATH: '/path/to/backend'
    }
  }]
};
EOF

# 启动应用
pm2 start ecosystem.config.js

# 查看状态
pm2 status

# 查看日志
pm2 logs skillseekers-backend
```

#### 使用Systemd (Linux)

```bash
# 创建systemd服务文件
sudo tee /etc/systemd/system/skillseekers-backend.service > /dev/null <<EOF
[Unit]
Description=SkillSeekers Backend
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment=PATH=/path/to/backend/venv/bin
ExecStart=/path/to/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start skillseekers-backend

# 设置开机自启
sudo systemctl enable skillseekers-backend

# 查看状态
sudo systemctl status skillseekers-backend

# 查看日志
sudo journalctl -u skillseekers-backend -f
```

## 5. 辅助服务启动

### 5.1 PostgreSQL

#### 直接启动

```bash
# Ubuntu/Debian
sudo systemctl start postgresql
sudo systemctl enable postgresql

# CentOS/RHEL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS
brew services start postgresql
```

#### Docker启动

```bash
docker run -d \
  --name postgres \
  -e POSTGRES_DB=skillseekers \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:14
```

### 5.2 Redis

#### 直接启动

```bash
# Ubuntu/Debian
sudo systemctl start redis
sudo systemctl enable redis

# CentOS/RHEL
sudo systemctl start redis
sudo systemctl enable redis

# macOS
brew services start redis
```

#### Docker启动

```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 5.3 MinIO

#### 直接启动

```bash
# 下载并启动MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
./minio server /data --console-address ":9001"
```

#### Docker启动

```bash
docker run -d \
  --name minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -p 9000:9000 \
  -p 9001:9001 \
  -v /data:/data \
  minio/minio server /data --console-address ":9001"
```

## 6. 完整启动流程

### 6.1 一键启动脚本 (开发环境)

创建 `start.sh`:

```bash
#!/bin/bash

echo "🚀 启动技能管理系统后端..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，创建中..."
    python -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo "📦 检查依赖..."
pip install -r requirements.txt

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️ .env文件不存在，使用默认配置"
    cp .env.example .env
fi

# 检查数据库
echo "🗄️ 检查数据库..."
if ! pg_isready -h localhost -p 5432 -U postgres &> /dev/null; then
    echo "❌ PostgreSQL未启动"
    exit 1
fi

# 运行迁移
echo "🔄 运行数据库迁移..."
alembic upgrade head

# 启动服务
echo "✅ 启动开发服务器..."
echo "📍 访问地址: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "🔍 停止服务: Ctrl+C"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

使用方式:

```bash
chmod +x start.sh
./start.sh
```

### 6.2 Docker Compose 完整启动

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: skillseekers
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d skillseekers"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  minio:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/skillseekers
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
      - MINIO_BUCKET=skill-files
      - DEBUG=True
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    volumes:
      - ./app:/app/app
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

volumes:
  postgres_data:
  minio_data:
```

启动:

```bash
docker-compose up -d
```

## 7. 验证启动

### 7.1 检查服务状态

```bash
# 检查API是否启动
curl http://localhost:8000/health

# 或打开浏览器访问
http://localhost:8000/docs
```

### 7.2 检查数据库连接

```bash
# 连接数据库
psql postgresql://user:password@localhost:5432/skillseekers

# 检查表
\dt
```

### 7.3 检查Redis

```bash
# 连接Redis
redis-cli

# 检查连接
ping
```

### 7.4 检查MinIO

```bash
# 访问MinIO控制台
http://localhost:9001
# 用户名: minioadmin
# 密码: minioadmin
```

## 8. 常见问题

### Q1: 端口被占用

```bash
# 查看端口占用
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

### Q2: 数据库连接失败

```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 重启PostgreSQL
sudo systemctl restart postgresql
```

### Q3: 虚拟环境激活失败

```bash
# 删除旧虚拟环境
rm -rf venv

# 重新创建
python -m venv venv
source venv/bin/activate
```

### Q4: 依赖安装失败

```bash
# 升级pip
pip install --upgrade pip

# 使用清华镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 9. 监控和日志

### 9.1 查看日志

```bash
# 开发模式日志
tail -f logs/app.log

# Docker日志
docker-compose logs -f backend
```

### 9.2 健康检查

```bash
# API健康检查
curl http://localhost:8000/health

# 数据库健康检查
curl http://localhost:8000/health/db

# Redis健康检查
curl http://localhost:8000/health/redis
```

### 9.3 性能监控

```bash
# 安装监控工具
pip install prometheus-client

# 查看应用指标
curl http://localhost:8000/metrics
```

## 10. 停止服务

### 10.1 停止开发服务

```bash
# 在终端中按 Ctrl+C
```

### 10.2 停止Docker服务

```bash
docker-compose down
```

### 10.3 停止后台服务

```bash
# 使用PM2
pm2 stop skillseekers-backend

# 使用Systemd
sudo systemctl stop skillseekers-backend
```

## 11. 生产部署建议

### 11.1 使用Nginx反向代理

创建Nginx配置 `/etc/nginx/sites-available/skillseekers`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

启用配置:

```bash
sudo ln -s /etc/nginx/sites-available/skillseekers /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 11.2 使用HTTPS

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 其他配置...
}
```

### 11.3 使用PM2管理生产服务

```bash
# 创建ecosystem.config.js
module.exports = {
  apps: [{
    name: 'skillseekers-backend',
    script: 'gunicorn',
    args: 'app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000',
    cwd: '/path/to/backend',
    interpreter: '/path/to/backend/venv/bin/python',
    instances: 1,
    exec_mode: 'fork',
    env: {
      NODE_ENV: 'production'
    }
  }]
};

# 启动
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 12. 快速启动命令

```bash
# 最快方式：使用Makefile
make setup    # 安装依赖
make migrate   # 运行迁移
make run-dev  # 启动开发服务

# 或使用Docker Compose
docker-compose up -d
```

## 总结

✅ **推荐启动方式**:
1. **开发环境**: 使用 `uvicorn app.main:app --reload`
2. **生产环境**: 使用 `docker-compose up -d`
3. **后台服务**: 使用 PM2 或 Systemd

📍 **重要地址**:
- API: http://localhost:8000
- API文档: http://localhost:8000/docs
- MinIO控制台: http://localhost:9001
- 数据库: localhost:5432
- Redis: localhost:6379

🎉 **启动成功后即可开始使用！**
