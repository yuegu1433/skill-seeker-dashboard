@echo off
chcp 65001 > nul

:: 技能管理系统 - 后端开发环境启动脚本 (Windows)

setlocal enabledelayedexpansion

:: 颜色定义
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "PURPLE=[95m"
set "CYAN=[96m"
set "WHITE=[97m"
set "BOLD=[1m"
set "NC=[0m"

:: 打印函数
:print_colored
echo %~2%~1%NC%
goto :eof

:print_header
call :print_colored "" %BLUE%
call :print_colored "========================================" %BLUE%
call :print_colored "🚀 技能管理系统 - 后端开发服务器" %BOLD%%BLUE%
call :print_colored "========================================" %BLUE%
echo.
goto :eof

:print_step
call :print_colored "[%~1] %~2" %CYAN%
goto :eof

:print_success
call :print_colored "✅ %~1" %GREEN%
goto :eof

:print_warning
call :print_colored "⚠️ %~1" %YELLOW%
goto :eof

:print_error
call :print_colored "❌ %~1" %RED%
goto :eof

:: 检查Python
:check_python
call :print_step "1" "检查Python版本"

python --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Python未安装或未添加到PATH"
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
call :print_success "Python版本: !PYTHON_VERSION!"
goto :eof

:: 检查虚拟环境
:check_virtual_env
call :print_step "2" "检查虚拟环境"

if not exist "venv" (
    call :print_warning "虚拟环境不存在，创建中..."
    python -m venv venv
    call :print_success "虚拟环境创建完成"
) else (
    call :print_success "虚拟环境已存在"
)
goto :eof

:: 安装依赖
:install_dependencies
call :print_step "3" "检查和安装依赖"

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 升级pip
echo 升级pip...
python -m pip install --upgrade pip >nul 2>&1
call :print_success "pip已升级"

:: 检查requirements.txt
if not exist "requirements.txt" (
    call :print_warning "requirements.txt不存在，创建基本依赖..."
    (
        echo fastapi==0.104.1
        echo uvicorn[standard]==0.24.0
        echo pydantic==2.5.0
        echo SQLAlchemy==2.0.23
        echo alembic==1.13.0
        echo psycopg2-binary==2.9.9
        echo redis==5.0.1
        echo python-multipart==0.0.6
        echo python-jose[cryptography]==3.3.0
        echo passlib[bcrypt]==1.7.4
        echo python-dotenv==1.0.0
        echo minio==7.2.0
        echo celery==5.3.4
        echo prometheus-client==0.19.0
    ) > requirements.txt
    call :print_success "requirements.txt已创建"
)

:: 安装依赖
echo 安装依赖包...
python -m pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    call :print_error "依赖安装失败"
    exit /b 1
)
call :print_success "依赖安装完成"
goto :eof

:: 设置环境变量
:setup_environment
call :print_step "4" "检查环境配置"

if not exist ".env" (
    if exist ".env.example" (
        call :print_warning ".env不存在，从模板复制..."
        copy .env.example .env >nul
        call :print_success ".env已创建，请根据需要修改配置"
    ) else (
        call :print_warning ".env不存在，使用默认配置"
        (
            echo # 数据库配置
            echo DATABASE_URL=sqlite:///./skillseekers.db
            echo.
            echo # API配置
            echo API_HOST=0.0.0.0
            echo API_PORT=8000
            echo DEBUG=True
            echo.
            echo # 安全配置
            echo SECRET_KEY=your-secret-key-change-in-production
            echo ALGORITHM=HS256
            echo ACCESS_TOKEN_EXPIRE_MINUTES=30
            echo.
            echo # 日志配置
            echo LOG_LEVEL=INFO
        ) > .env
        call :print_success ".env已创建"
    )
) else (
    call :print_success ".env已存在"
)
goto :eof

:: 创建目录
:create_directories
call :print_step "5" "创建必要目录"

if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "static" mkdir static

call :print_success "目录创建完成"
goto :eof

:: 检查FastAPI应用
:check_fastapi_app
call :print_step "6" "检查FastAPI应用"

if not exist "app\main.py" (
    call :print_warning "app\main.py不存在，创建基础FastAPI应用..."
    if not exist "app" mkdir app

    (
        echo from fastapi import FastAPI
        echo from fastapi.middleware.cors import CORSMiddleware
        echo from fastapi.responses import JSONResponse
        echo import uvicorn
        echo.
        echo app = FastAPI(
        echo     title=^"技能管理系统 API^",
        echo     description=^"技能管理系统的后端API服务^",
        echo     version=^"1.0.0^",
        echo ^)
        echo.
        echo # 添加CORS中间件
        echo app.add_middleware^(
        echo     CORSMiddleware,
        echo     allow_origins=[^"*^"],
        echo     allow_credentials=True,
        echo     allow_methods=[^"*^"],
        echo     allow_headers=[^"*^"],
        echo ^)
        echo.
        echo @app.get(^"/^")
        echo async def root^(^):
        echo     return {^"message^": ^"技能管理系统 API^", ^"status^": ^"running^"}
        echo.
        echo @app.get(^"/health^")
        echo async def health_check^(^):
        echo     return {^"status^": ^"healthy^"}
        echo.
        echo @app.get(^"/api/skills^")
        echo async def get_skills^(^):
        echo     return {^"data^": [], ^"total^": 0}
        echo.
        echo if __name__ == ^"__main__^":
        echo     uvicorn.run^(app, host=^"0.0.0.0^", port=8000^)
    ) > app\main.py

    call :print_success "基础FastAPI应用已创建"
) else (
    call :print_success "FastAPI应用存在"
)
goto :eof

:: 检查端口
:check_port
netstat -an | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    call :print_error "端口8000已被占用"
    call :print_error "请关闭占用端口的进程或修改端口"
    exit /b 1
)
goto :eof

:: 启动服务器
:start_server
call :print_step "7" "启动开发服务器"

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 检查端口
call :check_port
if errorlevel 1 exit /b 1

call :print_success "启动开发服务器..."
echo.
echo ========================================
call :print_colored "📍 服务器地址: http://localhost:8000" %GREEN%
call :print_colored "📚 API文档: http://localhost:8000/docs" %GREEN%
call :print_colored "🔍 停止服务: Ctrl+C" %YELLOW%
echo ========================================
echo.

:: 启动服务器
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
goto :eof

:: 停止服务器
:stop_server
call :print_colored "🛑 停止服务器..." %YELLOW%
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
call :print_success "服务器已停止"
goto :eof

:: 检查状态
:check_status
call :print_step "检查服务器状态"
netstat -an | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    call :print_success "服务器正在运行 (端口8000)"
) else (
    call :print_warning "服务器未运行"
)
goto :eof

:: 显示帮助
:show_help
echo 技能管理系统 - 后端启动脚本
echo.
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo   start       启动开发服务器 (默认)
echo   stop        停止服务器
echo   restart     重启服务器
echo   status      检查服务器状态
echo   help        显示此帮助信息
echo.
goto :eof

:: 主函数
:main
call :print_header

set "ACTION=%~1"
if "%ACTION%"=="" set "ACTION=start"

if "%ACTION%"=="start" (
    call :check_python
    if errorlevel 1 exit /b 1
    call :check_virtual_env
    call :install_dependencies
    call :setup_environment
    call :create_directories
    call :check_fastapi_app
    call :start_server
) else if "%ACTION%"=="stop" (
    call :stop_server
) else if "%ACTION%"=="restart" (
    call :stop_server
    timeout /t 2 >nul
    call :start_server
) else if "%ACTION%"=="status" (
    call :check_status
) else if "%ACTION%"=="help" (
    call :show_help
) else (
    call :print_error "未知选项: %ACTION%"
    call :show_help
    exit /b 1
)

goto :eof

:: 运行主函数
call :main %*
