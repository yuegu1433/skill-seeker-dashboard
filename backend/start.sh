#!/bin/bash

# 技能管理系统 - 后端开发环境启动脚本
# 适用于Linux和macOS

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 打印彩色文本
print_colored() {
    echo -e "${2}${1}${NC}"
}

# 打印标题
print_header() {
    echo ""
    print_colored "========================================" $BLUE
    print_colored "🚀 技能管理系统 - 后端开发服务器" $BOLD $BLUE
    print_colored "========================================" $BLUE
    echo ""
}

# 打印步骤
print_step() {
    print_colored "[$1] $2" $CYAN
}

# 打印成功
print_success() {
    print_colored "✅ $1" $GREEN
}

# 打印警告
print_warning() {
    print_colored "⚠️  $1" $YELLOW
}

# 打印错误
print_error() {
    print_colored "❌ $1" $RED
}

# 检查Python版本
check_python() {
    print_step "1" "检查Python版本"

    if ! command -v python3 &> /dev/null; then
        print_error "Python3未安装"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.9"

    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Python版本过低: $PYTHON_VERSION (需要3.9+)"
        exit 1
    fi

    print_success "Python版本: $PYTHON_VERSION"
}

# 检查虚拟环境
check_virtual_env() {
    print_step "2" "检查虚拟环境"

    if [ ! -d "venv" ]; then
        print_warning "虚拟环境不存在，创建中..."
        python3 -m venv venv
        print_success "虚拟环境创建完成"
    else
        print_success "虚拟环境已存在"
    fi
}

# 安装依赖
install_dependencies() {
    print_step "3" "检查和安装依赖"

    # 激活虚拟环境
    source venv/bin/activate

    # 升级pip
    echo "升级pip..."
    pip install --upgrade pip > /dev/null 2>&1
    print_success "pip已升级"

    # 检查requirements.txt
    if [ ! -f "requirements.txt" ]; then
        print_warning "requirements.txt不存在，创建基本依赖..."
        cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
SQLAlchemy==2.0.23
alembic==1.13.0
psycopg2-binary==2.9.9
redis==5.0.1
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
minio==7.2.0
celery==5.3.4
prometheus-client==0.19.0
EOF
        print_success "requirements.txt已创建"
    fi

    # 安装依赖
    echo "安装依赖包..."
    pip install -r requirements.txt > /dev/null 2>&1
    print_success "依赖安装完成"
}

# 设置环境变量
setup_environment() {
    print_step "4" "检查环境配置"

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env不存在，从模板复制..."
            cp .env.example .env
            print_success ".env已创建，请根据需要修改配置"
        else
            print_warning ".env不存在，使用默认配置"
            cat > .env << EOF
# 数据库配置
DATABASE_URL=sqlite:///./skillseekers.db

# API配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# 安全配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 日志配置
LOG_LEVEL=INFO
EOF
            print_success ".env已创建"
        fi
    else
        print_success ".env已存在"
    fi
}

# 创建目录
create_directories() {
    print_step "5" "创建必要目录"
    mkdir -p logs uploads static
    print_success "目录创建完成"
}

# 检查FastAPI应用
check_fastapi_app() {
    print_step "6" "检查FastAPI应用"

    if [ ! -f "app/main.py" ]; then
        print_warning "app/main.py不存在，创建基础FastAPI应用..."
        mkdir -p app

        cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(
    title="技能管理系统 API",
    description="技能管理系统的后端API服务",
    version="1.0.0",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "技能管理系统 API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/skills")
async def get_skills():
    return {"data": [], "total": 0}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
        print_success "基础FastAPI应用已创建"
    else
        print_success "FastAPI应用存在"
    fi
}

# 检查端口
check_port() {
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "端口8000已被占用"
        print_error "请关闭占用端口的进程或修改端口"
        return 1
    fi
    return 0
}

# 启动服务器
start_server() {
    print_step "7" "启动开发服务器"

    # 激活虚拟环境
    source venv/bin/activate

    # 检查端口
    if ! check_port; then
        exit 1
    fi

    print_success "启动开发服务器..."
    echo ""
    echo "========================================"
    print_colored "📍 服务器地址: http://localhost:8000" $GREEN
    print_colored "📚 API文档: http://localhost:8000/docs" $GREEN
    print_colored "🔍 停止服务: Ctrl+C" $YELLOW
    echo "========================================"
    echo ""

    # 启动服务器
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# 停止服务器
stop_server() {
    print_colored "🛑 停止服务器..." $YELLOW
    pkill -f "uvicorn app.main:app" || true
    print_success "服务器已停止"
}

# 显示帮助信息
show_help() {
    echo "技能管理系统 - 后端启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start       启动开发服务器 (默认)"
    echo "  stop        停止服务器"
    echo "  restart     重启服务器"
    echo "  status      检查服务器状态"
    echo "  help        显示此帮助信息"
    echo ""
}

# 检查服务器状态
check_status() {
    print_step "检查服务器状态"

    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_success "服务器正在运行 (端口8000)"
    else
        print_warning "服务器未运行"
    fi
}

# 主函数
main() {
    print_header

    case "${1:-start}" in
        start)
            # 执行启动步骤
            check_python
            check_virtual_env
            install_dependencies
            setup_environment
            create_directories
            check_fastapi_app
            start_server
            ;;
        stop)
            stop_server
            ;;
        restart)
            stop_server
            sleep 2
            exec "$0" start
            ;;
        status)
            check_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 捕获中断信号
trap 'echo ""; print_success "已取消启动"; exit 0' INT

# 运行主函数
main "$@"
