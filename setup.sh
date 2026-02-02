#!/bin/bash

# 技能管理系统 - 自动化安装脚本
# 一键安装和配置所有依赖

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 打印函数
print_colored() {
    echo -e "${2}${1}${NC}"
}

print_header() {
    echo ""
    print_colored "╔═══════════════════════════════════════════════════════╗" $BLUE
    print_colored "║           技能管理系统 - 自动化安装程序              ║" $BOLD $BLUE
    print_colored "╚═══════════════════════════════════════════════════════╝" $BLUE
    echo ""
}

print_step() {
    print_colored "➤ $1" $CYAN
}

print_success() {
    print_colored "✓ $1" $GREEN
}

print_warning() {
    print_colored "⚠ $1" $YELLOW
}

print_error() {
    print_colored "✗ $1" $RED
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查Python
check_python() {
    print_step "检查Python环境..."

    if ! command_exists python3; then
        print_error "Python3未安装"
        print_error "请先安装Python 3.9+"
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

# 检查Node.js
check_nodejs() {
    print_step "检查Node.js环境..."

    if ! command_exists node; then
        print_warning "Node.js未安装"
        print_warning "前端功能需要Node.js 16+"
        echo "请访问: https://nodejs.org/"
        return 1
    fi

    NODE_VERSION=$(node -v)
    print_success "Node.js版本: $NODE_VERSION"
}

# 检查Docker
check_docker() {
    print_step "检查Docker环境..."

    if ! command_exists docker; then
        print_warning "Docker未安装 (可选)"
        print_warning "可使用Docker启动完整环境"
        return 1
    fi

    if ! command_exists docker-compose; then
        print_warning "Docker Compose未安装"
        return 1
    fi

    print_success "Docker环境正常"
}

# 安装Python依赖
install_python_deps() {
    print_step "安装Python依赖..."

    cd backend

    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        print_warning "创建虚拟环境..."
        python3 -m venv venv
        print_success "虚拟环境创建完成"
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 升级pip
    echo "升级pip..."
    pip install --upgrade pip >/dev/null 2>&1

    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt >/dev/null 2>&1
        print_success "Python依赖安装完成"
    else
        print_warning "requirements.txt不存在，跳过依赖安装"
    fi

    cd ..
}

# 安装Node.js依赖
install_nodejs_deps() {
    print_step "安装Node.js依赖..."

    if [ -d "frontend" ]; then
        cd frontend

        if [ -f "package.json" ]; then
            # 检查npm
            if command_exists npm; then
                echo "安装npm依赖..."
                npm install >/dev/null 2>&1
                print_success "Node.js依赖安装完成"
            else
                print_warning "npm未找到，跳过前端依赖安装"
            fi
        else
            print_warning "package.json不存在，跳过前端依赖安装"
        fi

        cd ..
    else
        print_warning "frontend目录不存在，跳过前端依赖安装"
    fi
}

# 设置环境变量
setup_env() {
    print_step "设置环境变量..."

    # 后端环境
    if [ -d "backend" ]; then
        cd backend
        if [ ! -f ".env" ]; then
            if [ -f ".env.example" ]; then
                cp .env.example .env
                print_success "后端.env文件已创建"
            else
                print_warning "后端.env.example不存在"
            fi
        else
            print_success "后端.env文件已存在"
        fi
        cd ..
    fi

    # 前端环境 (可选)
    if [ -d "frontend" ]; then
        cd frontend
        if [ ! -f ".env.local" ]; then
            cat > .env.local << EOF
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOF
            print_success "前端.env.local文件已创建"
        else
            print_success "前端.env.local文件已存在"
        fi
        cd ..
    fi
}

# 创建必要目录
create_dirs() {
    print_step "创建必要目录..."

    mkdir -p backend/logs backend/uploads backend/static
    mkdir -p frontend/dist frontend/build

    print_success "目录创建完成"
}

# 设置脚本权限
setup_permissions() {
    print_step "设置脚本权限..."

    chmod +x backend/start.sh 2>/dev/null || true
    chmod +x setup.sh

    print_success "权限设置完成"
}

# 生成启动脚本
generate_scripts() {
    print_step "生成便捷脚本..."

    # 生成快速启动脚本
    cat > quick-start.sh << 'EOF'
#!/bin/bash

# 快速启动脚本

echo "🚀 启动技能管理系统..."

# 启动后端
echo "启动后端服务..."
cd backend
if [ -f "start_dev.py" ]; then
    python start_dev.py &
    BACKEND_PID=$!
else
    echo "错误: 未找到后端启动脚本"
    exit 1
fi

# 等待后端启动
sleep 5

# 启动前端
echo "启动前端服务..."
cd ../frontend
if [ -f "package.json" ]; then
    npm run dev &
    FRONTEND_PID=$!
else
    echo "错误: 未找到前端配置"
    exit 1
fi

echo ""
echo "✓ 系统启动完成!"
echo "📍 前端地址: http://localhost:3001"
echo "📚 API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待中断
trap "echo ''; echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

wait
EOF

    chmod +x quick-start.sh

    # 生成停止脚本
    cat > quick-stop.sh << 'EOF'
#!/bin/bash

echo "🛑 停止技能管理系统..."

# 杀死Python进程
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "python.*start_dev" 2>/dev/null || true

# 杀死Node进程
pkill -f "npm.*dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

# 停止Docker服务
docker-compose down 2>/dev/null || true

echo "✓ 所有服务已停止"
EOF

    chmod +x quick-stop.sh

    print_success "便捷脚本生成完成"
}

# 显示完成信息
show_completion() {
    echo ""
    print_colored "╔═══════════════════════════════════════════════════════╗" $GREEN
    print_colored "║                  安装完成! 🎉                       ║" $BOLD $GREEN
    print_colored "╚═══════════════════════════════════════════════════════╝" $GREEN
    echo ""
    print_colored "可用的启动方式:" $BOLD
    echo ""
    print_colored "1. 一键启动:" $CYAN
    echo "   ./quick-start.sh"
    echo ""
    print_colored "2. 分别启动:" $CYAN
    echo "   后端: cd backend && python start_dev.py"
    echo "   前端: cd frontend && npm run dev"
    echo ""
    print_colored "3. Docker启动:" $CYAN
    echo "   docker-compose up -d"
    echo ""
    print_colored "访问地址:" $BOLD
    echo ""
    print_colored "• 前端页面: http://localhost:3001" $YELLOW
    print_colored "• API文档:  http://localhost:8000/docs" $YELLOW
    print_colored "• MinIO:     http://localhost:9001" $YELLOW
    echo ""
    print_colored "停止服务: ./quick-stop.sh" $CYAN
    echo ""
    print_colored "详细说明请查看: QUICK_START_GUIDE.md" $CYAN
    echo ""
}

# 主函数
main() {
    print_header

    # 执行安装步骤
    check_python
    check_nodejs
    check_docker

    echo ""
    print_colored "开始安装依赖..." $BOLD
    echo ""

    install_python_deps
    install_nodejs_deps
    setup_env
    create_dirs
    setup_permissions
    generate_scripts

    show_completion
}

# 运行主函数
main "$@"
