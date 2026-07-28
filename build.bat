@echo off
chcp 65001 >nul
title NetTools - 打包工具

echo ============================================
echo   NetTools - 网络工程师工具箱 打包脚本
echo   安全优化版 - 减少安全软件误报
echo ============================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/5] 检查 Python 环境...
python --version

echo.
echo [2/5] 安装依赖...
pip install -r requirements.txt -q

echo.
echo [3/5] 清理旧的构建文件...
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul

echo.
echo [4/5] 打包 NetTools.exe ...
echo   提示: 首次打包约需 1-3 分钟，请耐心等待...
echo.
python -m PyInstaller NetTools.spec --clean --noconfirm --log-level=WARN

if %errorlevel% equ 0 (
    echo.
    echo [5/5] 打包为发布压缩包...
    cd dist
    powershell -Command "Compress-Archive -Path 'NetTools\*' -DestinationPath 'NetTools_v1.3.zip' -Force"
    cd ..
    
    echo.
    echo ============================================
    echo   打包成功！
    echo   输出目录: dist\NetTools\
    echo   主程序:   dist\NetTools\NetTools.exe
    echo   压缩包:   dist\NetTools_v1.3.zip
    echo ============================================
    echo.
    echo 分发方式:
    echo   1. 将 dist\NetTools 整个文件夹复制给其他人
    echo   2. 或解压 dist\NetTools_v1.3.zip 即可使用
    echo.
    echo 安全优化:
    echo   - onedir 目录模式（非 onefile 单文件）
    echo   - 嵌入合法版本信息（右键-属性查看）
    echo   - UPX 压缩 + 去除调试符号
    echo   - 纯网络工具，无敏感行为
    echo.
    echo 如被误报：请将 NetTools.exe 提交到安全厂商白名单
) else (
    echo.
    echo ============================================
    echo   打包失败，请检查错误信息
    echo ============================================
)

echo.
echo 按任意键退出...
pause >nul
