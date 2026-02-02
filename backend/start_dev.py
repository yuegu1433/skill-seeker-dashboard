#!/usr/bin/env python3
"""
技能管理系统 - 开发环境启动脚本

快速启动后端开发服务，包含依赖检查、环境配置、服务验证等功能
"""

import os
import sys
import subprocess
import time
import signal
import socket
from pathlib import Path

# 颜色输出
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_colored(text, color=Colors.WHITE):
    """打印彩色文本"""
    print(f"{color}{text}{Colors.END}")

def print_header():
    """打印标题"""
    print_colored("=" * 60, Colors.BLUE)
    print_colored("🚀 技能管理系统 - 后端开发服务器", Colors.BOLD + Colors.BLUE)
    print_colored("=" * 60, Colors.BLUE)
    print()

def print_step(step, description):
    """打印步骤"""
    print_colored(f"[{step}] {description}", Colors.CYAN)

def print_success(message):
    """打印成功信息"""
    print_colored(f"✅ {message}", Colors.GREEN)

def print_warning(message):
    """打印警告信息"""
    print_colored(f"⚠️ {message}", Colors.YELLOW)

def print_error(message):
    """打印错误信息"""
    print_colored(f"❌ {message}", Colors.RED)

def check_python():
    """检查Python版本"""
    print_step("1", "检查Python版本")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print_error(f"Python版本过低: {version.major}.{version.minor}")
        print_error("需要Python 3.9+")
        return False
    print_success(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_port(port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def check_virtual_env():
    """检查虚拟环境"""
    print_step("2", "检查虚拟环境")
    venv_path = Path("venv")
    if not venv_path.exists():
        print_warning("虚拟环境不存在，创建中...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_success("虚拟环境创建完成")
    else:
        print_success("虚拟环境已存在")
    return True

def get_venv_python():
    """获取虚拟环境Python路径"""
    if os.name == 'nt':  # Windows
        return "venv\\Scripts\\python.exe"
    else:  # Linux/Mac
        return "venv/bin/python"

def install_dependencies():
    """安装依赖"""
    print_step("3", "检查和安装依赖")
    python = get_venv_python()

    # 检查requirements.txt是否存在
    if not Path("requirements.txt").exists():
        print_warning("requirements.txt不存在，创建基本依赖...")
        with open("requirements.txt", "w") as f:
            f.write("""fastapi==0.104.1
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
""")
        print_success("requirements.txt已创建")

    # 升级pip
    print("升级pip...", end=" ")
    subprocess.run([python, "-m", "pip", "install", "--upgrade", "pip"],
                  capture_output=True, text=True)
    print_success("pip已升级")

    # 安装依赖
    print("安装依赖包...", end=" ")
    result = subprocess.run(
        [python, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print_error("依赖安装失败")
        print_error(result.stderr)
        return False
    print_success("依赖安装完成")
    return True

def setup_environment():
    """设置环境变量"""
    print_step("4", "检查环境配置")
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path(".env.example")
        if env_example.exists():
            print_warning(".env不存在，从模板复制...")
            subprocess.run(["cp", ".env.example", ".env"])
            print_success(".env已创建，请根据需要修改配置")
        else:
            print_warning(".env不存在，使用默认配置")
    else:
        print_success(".env已存在")
    return True

def check_services():
    """检查辅助服务"""
    print_step("5", "检查辅助服务")

    # 检查PostgreSQL
    try:
        import psycopg2
        print_success("PostgreSQL: 已安装")
    except ImportError:
        print_warning("PostgreSQL: 未安装 (如果使用数据库，请安装 psycopg2-binary)")

    # 检查Redis
    try:
        import redis
        print_success("Redis: 已安装")
    except ImportError:
        print_warning("Redis: 未安装 (如果使用缓存，请安装 redis)")

    return True

def create_directories():
    """创建必要目录"""
    print_step("6", "创建必要目录")
    dirs = ["logs", "uploads", "static"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print_success("目录创建完成")
    return True

def check_fastapi_app():
    """检查FastAPI应用"""
    print_step("7", "检查FastAPI应用")
    app_file = Path("app/main.py")
    if not app_file.exists():
        print_warning("app/main.py不存在，创建基础FastAPI应用...")
        app_file.parent.mkdir(exist_ok=True)

        # 创建基础应用
        app_code = """from fastapi import FastAPI
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
"""
        with open("app/main.py", "w") as f:
            f.write(app_code)
        print_success("基础FastAPI应用已创建")
    else:
        print_success("FastAPI应用存在")
    return True

def run_migrations():
    """运行数据库迁移"""
    print_step("8", "运行数据库迁移")
    python = get_venv_python()

    # 检查alembic配置
    if not Path("alembic.ini").exists():
        print_warning("Alembic配置不存在，跳过迁移...")
        return True

    # 初始化Alembic
    if not Path("alembic/env.py").exists():
        print("初始化Alembic...", end=" ")
        subprocess.run([python, "-m", "alembic", "init", "alembic"],
                      capture_output=True)
        print_success("初始化完成")

    # 运行迁移
    print("运行数据库迁移...", end=" ")
    result = subprocess.run([python, "-m", "alembic", "upgrade", "head"],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print_warning("迁移失败 (可能需要先配置数据库)")
    else:
        print_success("迁移完成")
    return True

def start_server():
    """启动开发服务器"""
    print_step("9", "启动开发服务器")

    # 检查端口
    if not check_port(8000):
        print_error("端口8000已被占用")
        print_error("请关闭占用端口的进程或修改端口")
        return False

    python = get_venv_python()
    print_success("启动开发服务器...")
    print()
    print_colored("=" * 60, Colors.BLUE)
    print_colored("📍 服务器地址: http://localhost:8000", Colors.GREEN)
    print_colored("📚 API文档: http://localhost:8000/docs", Colors.GREEN)
    print_colored("🔍 停止服务: Ctrl+C", Colors.YELLOW)
    print_colored("=" * 60, Colors.BLUE)
    print()

    # 启动服务器
    try:
        subprocess.run([python, "-m", "uvicorn", "app.main:app",
                        "--reload", "--host", "0.0.0.0", "--port", "8000"])
    except KeyboardInterrupt:
        print()
        print_success("服务器已停止")

def main():
    """主函数"""
    print_header()

    # 检查步骤
    steps = [
        check_python,
        check_virtual_env,
        install_dependencies,
        setup_environment,
        check_services,
        create_directories,
        check_fastapi_app,
        run_migrations,
    ]

    for step in steps:
        try:
            if not step():
                print_error("启动失败")
                return False
            time.sleep(0.5)  # 短暂延迟
        except Exception as e:
            print_error(f"执行步骤时出错: {e}")
            return False

    # 启动服务器
    start_server()

    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print()
        print_success("已取消启动")
        sys.exit(0)
    except Exception as e:
        print_error(f"启动失败: {e}")
        sys.exit(1)
