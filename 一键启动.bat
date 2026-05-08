@echo off
cd /d "%~dp0"

echo.
echo   ╔══════════════════════════════════╗
echo   ║      呱 智 能 鲸 鱼            ║
echo   ║   deepseek-cn v0.1.0           ║
echo   ║   终端里的中文编程搭子          ║
echo   ╚══════════════════════════════════╝
echo.

echo [1/3] 检测 Python 环境...

set PYTHON_CMD=

where python >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=python & goto :check_python_ver

where python3 >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=python3 & goto :check_python_ver

where py >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=py & goto :check_python_ver

echo   X 未找到 Python
echo   >> 请安装 Python 3.10+
echo   >> https://www.python.org/downloads/
echo.
pause
exit /b 1

:check_python_ver
call %PYTHON_CMD% --version
echo   OK Python 已就绪
echo.

echo [2/3] 检测依赖包...

call %PYTHON_CMD% -c "import textual, openai" >nul 2>&1
if not errorlevel 1 (
    echo   OK 依赖包已就绪
    goto :deps_ok
)

echo   >> 正在安装依赖包...
echo.
call %PYTHON_CMD% -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo   X 依赖安装失败
    pause
    exit /b 1
)
echo   OK 依赖安装完成
echo.

:deps_ok
echo [3/3] 正在启动智能鲸鱼...
echo.
echo   ----------------------------------------
echo   首次使用需要输入 DeepSeek API 密钥
echo   获取地址：platform.deepseek.com
echo   密钥保存在：%USERPROFILE%\.deepseek-cn\
echo   ----------------------------------------
echo.

call %PYTHON_CMD% -m 源码.主程序 %*

if errorlevel 1 (
    echo.
    echo   X 程序异常退出 (错误码: %errorlevel%)
    echo.
    echo   常见问题：
    echo   1. 密钥无效 - 删除 %USERPROFILE%\.deepseek-cn\config.json 重试
    echo   2. 网络问题 - 检查 api.deepseek.com 连通性
    echo   3. 终端兼容性 - 推荐用 Windows Terminal 运行
    echo.
)

echo.
echo   >> 按任意键关闭窗口...
pause >nul
