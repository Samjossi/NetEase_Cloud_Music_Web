#!/bin/bash
# 清理临时文件脚本

set -e

echo "开始清理临时文件..."

# 清理构建缓存
if [ -d "/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/build" ]; then
    echo "删除构建缓存..."
    rm -rf "/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/build"/*
    echo "构建缓存清理完成"
fi

# 清理临时目录
if [ -d "/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/packaging_04/temp" ]; then
    echo "删除临时目录..."
    rm -rf "/home/afro/heavenly_kingdom/do_for_fun/NetEase_Cloud_Music_Web/packaging_04/temp"/*
    echo "临时目录清理完成"
fi

# 清理PyInstaller缓存
echo "清理PyInstaller缓存..."
rm -rf ~/.cache/pyinstaller/* 2>/dev/null || true

echo "所有临时文件清理完成"
