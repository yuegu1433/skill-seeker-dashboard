@echo off
chcp 65001 > nul

:: 技能管理系统 - Windows自动化安装脚本

setlocal enabledelayedexpansion

set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "CYAN=[96m"
set "BOLD=[1m"
set "NC=[0m"

:print_colored
echo %~2%~1%NC%
goto :eof

:print_header
echo.
call :print_colored "╔═══════════════════════════════════════════════════════╗" %BLUE%
call :print_colored "║           技能管理系统 - 自动化安装程序            ║" %BOLD%%BLUE%
call :print_colored "╚═══════════════════════════════════════════════════════╝" %BLUE%
echo.
goto :eof

:print_step
call :print_colored "➤ %~1" %CYAN%
goto :eof

:print_success
call :print_colored "✓ %~1" %GREEN%
goto :eof

:print_warning
call :print_colored "⚠ %~1" %YELLOW%
goto :eof

:print_error
call :print_colored "✗ %~1" %RED%
goto :eof

:check_python
call :print_step "检查Python环境..."

python --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Python未安装"
    call :print_error "请从 https://python.org 下载安装Python 3.9+"
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
call :print_success "Python版本: !PYTHON_VERSION!"
goto :eof

:check_nodejs
call :print_step "检查Node.js环境..."

node --version >nul 2>&1
if errorlevel 1 (
    call :print_warning "Node.js未安装"
    call :print_warning "前端功能需要Node.js 16+"
    call :print_warning "请从 https://nodejs.org/ 下载安装"
    goto :eof
)

for /f %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
call :print_success "Node.js版本: !NODE_VERSION!"
goto :eof

:install_python_deps
call :print_step "安装Python依赖..."

cd backend

if not exist "venv" (
    call :print_warning "创建虚拟环境..."
    python -m venv venv
    call :print_success "虚拟环境创建完成"
)

call venv\Scripts\activate.bat

echo 升级pip...
python -m pip install --upgrade pip >nul 2>&1

if exist "requirements.txt" (
    echo 安装依赖...
    python -m pip install -r requirements.txt >nul 2>&1
    call :print_success "Python依赖安装完成"
) else (
    call :print_warning "requirements.txt不存在，跳过依赖安装"
)

cd ..
goto :eof

:install_nodejs_deps
call :print_step "安装Node.js依赖..."

if exist "frontend" (
    cd frontend

    if exist "package.json" (
        echo 安装npm依赖...
        npm install >nul 2>&1
        if errorlevel 1 (
            call :print_warning "npm安装失败，请检查npm版本"
        ) else (
            call :print_success "Node.js依赖安装完成"
        )
    ) else (
        call :print_warning "package.json不存在，跳过前端依赖安装"
    )

    cd ..
) else (
    call :print_warning "frontend目录不存在，跳过前端依赖安装"
)
goto :eof

:setup_env
call :print_step "设置环境变量..."

if exist "backend" (
    cd backend
    if not exist ".env" (
        if exist ".env.example" (
            copy .env.example .env >nul
            call :print_success "后端.env文件已创建"
        ) else (
            call :print_warning "后端.env.example不存在"
        )
    ) else (
        call :print_success "后端.env文件已存在"
    )
    cd ..
)

if exist "frontend" (
    cd frontend
    if not exist ".env.local" (
        (
            echo VITE_API_URL=http://localhost:8000
            echo VITE_WS_URL=ws://localhost:8000
        ) > .env.local
        call :print_success "前端.env.local文件已创建"
    ) else (
        call :print_success "前端.env.local文件已存在"
    )
    cd ..
)
goto :eof

:create_dirs
call :print_step "创建必要目录..."

if not exist "backend\logs" mkdir backend\logs
if not exist "backend\uploads" mkdir backend\uploads
if not exist "backend\static" mkdir backend\static
if not exist "frontend\dist" mkdir frontend\dist
if not exist "frontend\build" mkdir frontend\build

call :print_success "目录创建完成"
goto :eof

:generate_scripts
call :print_step "生成便捷脚本..."

:: 创建快速启动脚本
(
echo @echo off
echo chcp 65001 ^> nul
echo.
echo :: 快速启动脚本
echo.
echo echo 🚀 启动技能管理系统...
echo.
echo :: 启动后端
echo echo 启动后端服务...
echo cd backend
echo start "Backend" cmd /k "python start_dev.py"
echo.
echo echo 等待后端启动...
echo timeout /t 5 /nobreak ^>nul
echo.
echo :: 启动前端
echo echo 启动前端服务...
echo cd ..\frontend
echo start "Frontend" cmd /k "npm run dev"
echo.
echo echo.
echo echo ✓ 系统启动完成!
echo echo 📍 前端地址: http://localhost:3001
echo echo 📚 API文档:  http://localhost:8000/docs
echo echo.
echo pause
) > quick-start.bat

:: 创建停止脚本
(
echo @echo off
echo.
echo 🛑 停止技能管理系统...
echo.
echo taskkill /F /IM uvicorn.exe ^>nul 2^>^&1
echo taskkill /F /IM python.exe ^>nul 2^>^&1
echo taskkill /F /IM node.exe ^>nul 2^>^&1
echo taskkill /F /IM npm.cmd ^>nul 2^>^&1
echo.
echo ✓ 所有服务已停止
echo pause
) > quick-stop.bat

call :print_success "便捷脚本生成完成"
goto :eof

:show_completion
echo.
call :print_colored "╔═══════════════════════════════════════════════════════╗" %GREEN%
call :print_colored "║                  安装完成! 🎉                       ║" %BOLD%%GREEN%
call :print_colored "╚═══════════════════════════════════════════════════════╝" %GREEN%
echo.
call :print_colored "可用的启动方式:" %BOLD%
echo.
call :print_colored "1. 一键启动:" %CYAN%
echo    quick-start.bat
echo.
call :print_colored "2. 分别启动:" %CYAN%
echo    后端: cd backend && start.bat
echo    前端: cd frontend && npm run dev
echo.
call :print_colored "3. Docker启动:" %CYAN%
echo    docker-compose up -d
echo.
call :print_colored "访问地址:" %BOLD%
echo.
call :print_colored "• 前端页面: http://localhost:3001" %YELLOW%
call :print_colored "• API文档:  http://localhost:8000/docs" %YELLOW%
call :print_colored "• MinIO:     http://localhost:9001" %YELLOW%
echo.
call :print_colored "停止服务: quick-stop.bat" %CYAN%
echo.
call :print_colored "详细说明请查看: QUICK_START_GUIDE.md" %CYAN%
echo.
pause
goto :eof

:: 主函数
:call :main
call :print_header

call :check_python
call :check_nodejs

echo.
call :print_colored "开始安装依赖..." %BOLD%
echo.

call :install_python_deps
call :install_nodejs_deps
call :setup_env
call :create_dirs
call :generate_scripts

call :show_completion
