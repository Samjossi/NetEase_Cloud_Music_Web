#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易云音乐桌面版 - GUI打包管理器
提供统一的图形界面来管理各种打包模式
"""

import os
import sys
import subprocess
import threading
import time
from tkinter import ttk, messagebox, filedialog, scrolledtext
import tkinter as tk
from pathlib import Path

# 获取脚本目录
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DISH_DIR = PROJECT_ROOT / "dish"
BUILD_LOGS_DIR = PROJECT_ROOT / "build_logs"

class PackagingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("网易云音乐打包工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置窗口图标（如果存在）
        self.setup_window_icon()
        
        # 当前进程引用
        self.current_process = None
        self.output_thread = None
        
        # 创建界面
        self.create_widgets()
        
        # 检查环境
        self.check_environment()
    
    def setup_window_icon(self):
        """设置窗口图标"""
        try:
            icon_path = PROJECT_ROOT.parent / "icon" / "icon_48x48.png"
            if icon_path.exists():
                self.root.iconphoto(True, tk.PhotoImage(file=str(icon_path)))
        except Exception as e:
            print(f"设置窗口图标失败: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="wens")
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="网易云音乐桌面版打包工具", 
                              font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 打包模式选择
        mode_frame = ttk.LabelFrame(main_frame, text="打包模式", padding="10")
        mode_frame.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="quick")
        
        modes = [
            ("快速构建", "quick", "生成Linux可执行文件 (约213MB，需要系统Python 3.12.3+)"),
            ("AppImage构建", "appimage", "生成AppImage便携版 (约300-400MB，自包含环境)"),
            ("依赖检查", "check", "检查系统环境和依赖"),
            ("测试构建", "test", "测试已构建的文件"),
            ("清理临时文件", "clean", "清理构建缓存和临时文件")
        ]
        
        for i, (text, value, desc) in enumerate(modes):
            rb = ttk.Radiobutton(mode_frame, text=text, variable=self.mode_var, 
                               value=value, command=self.on_mode_change)
            rb.grid(row=i, column=0, sticky="w", pady=2)
            
            desc_label = ttk.Label(mode_frame, text=desc, font=("Arial", 9), 
                               foreground="gray")
            desc_label.grid(row=i, column=1, sticky="w", padx=(20, 0), pady=2)
        
        # 进度显示
        progress_frame = ttk.LabelFrame(main_frame, text="进度", padding="10")
        progress_frame.grid(row=2, column=0, columnspan=2, sticky="we", pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="就绪")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.grid(row=0, column=0, sticky="w")
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky="we", pady=(5, 0))
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="开始打包", 
                                  command=self.start_packaging)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="停止", 
                                 command=self.stop_packaging, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        self.open_button = ttk.Button(button_frame, text="打开输出目录", 
                                  command=self.open_output_dir)
        self.open_button.grid(row=0, column=2, padx=(0, 10))
        
        # 日志输出
        log_frame = ttk.LabelFrame(main_frame, text="日志输出", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky="wens", pady=(0, 10))
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky="wens")
        
        # 清空日志按钮
        clear_button = ttk.Button(log_frame, text="清空日志", 
                             command=self.clear_log)
        clear_button.grid(row=1, column=0, pady=(5, 0))
        
        # 配置主框架权重
        main_frame.rowconfigure(4, weight=1)  # 让日志区域可以扩展
    
    def on_mode_change(self):
        """模式改变时的处理"""
        mode = self.mode_var.get()
        if mode == "clean":
            self.progress_var.set("点击开始清理")
        else:
            self.progress_var.set("就绪")
    
    def check_environment(self):
        """检查环境"""
        self.log_message("正在检查环境...")
        
        # 检查脚本文件
        scripts = {
            "快速构建": SCRIPT_DIR / "quick_build.sh",
            "AppImage构建": SCRIPT_DIR / "build_appimage.sh", 
            "依赖检查": SCRIPT_DIR / "check_dependencies.sh",
            "测试": SCRIPT_DIR / "test_build.sh"
        }
        
        missing_scripts = []
        for name, script in scripts.items():
            if not script.exists():
                missing_scripts.append(f"{name}: {script}")
        
        if missing_scripts:
            self.log_message("警告: 发现缺失的脚本文件:", "ERROR")
            for script in missing_scripts:
                self.log_message(f"  - {script}", "ERROR")
        else:
            self.log_message("所有脚本文件检查通过")
        
        # 检查输出目录
        if not DISH_DIR.exists():
            DISH_DIR.mkdir(parents=True)
            self.log_message(f"创建输出目录: {DISH_DIR}")
        
        if not BUILD_LOGS_DIR.exists():
            BUILD_LOGS_DIR.mkdir(parents=True)
            self.log_message(f"创建日志目录: {BUILD_LOGS_DIR}")
        
        # 检查UV虚拟环境
        venv_path = PROJECT_ROOT.parent / ".venv"
        if venv_path.exists():
            self.log_message("UV虚拟环境检查通过")
        else:
            self.log_message("警告: 未找到UV虚拟环境", "WARNING")
        
        self.log_message("环境检查完成")
    
    def log_message(self, message, level="INFO"):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        
        # 根据级别设置颜色
        if level == "ERROR":
            tag = "error"
            prefix = "❌"
        elif level == "WARNING":
            tag = "warning" 
            prefix = "⚠️"
        elif level == "SUCCESS":
            tag = "success"
            prefix = "✅"
        else:
            tag = "info"
            prefix = "ℹ️"
        
        # 配置文本标签
        self.log_text.tag_configure(tag, foreground={
            "ERROR": "red",
            "WARNING": "orange", 
            "SUCCESS": "green",
            "INFO": "black"
        }.get(level, "black"))
        
        # 插入消息
        self.log_text.insert(tk.END, f"[{timestamp}] {prefix} {message}\n", tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_packaging(self):
        """开始打包过程"""
        if self.current_process and self.current_process.poll() is None:
            messagebox.showwarning("警告", "打包正在进行中，请等待完成")
            return
        
        mode = self.mode_var.get()
        
        # 确认对话框
        if mode == "clean":
            if not messagebox.askyesno("确认", "确定要清理所有临时文件和缓存吗？"):
                return
        elif mode in ["quick", "appimage"]:
            if not messagebox.askyesno("确认", f"确定要开始{self.get_mode_name(mode)}吗？\n\n这可能需要几分钟时间。"):
                return
        
        # 禁用开始按钮，启用停止按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 启动进度条
        self.progress_bar.start(10)
        self.progress_var.set(f"正在进行{self.get_mode_name(mode)}...")
        
        # 启动打包进程
        threading.Thread(target=self.run_packaging, args=(mode,), daemon=True).start()
    
    def stop_packaging(self):
        """停止打包过程"""
        if self.current_process:
            try:
                self.current_process.terminate()
                self.log_message("用户停止了打包过程", "WARNING")
            except Exception as e:
                self.log_message(f"停止过程失败: {e}", "ERROR")
        
        self.reset_ui()
    
    def run_packaging(self, mode):
        """运行打包进程"""
        try:
            # 根据模式选择脚本
            scripts = {
                "quick": "quick_build.sh",
                "appimage": "build_appimage.sh", 
                "check": "check_dependencies.sh",
                "test": "test_build.sh",
                "clean": "clean_temp_files.sh"
            }
            
            script_name = scripts.get(mode)
            if not script_name:
                self.log_message(f"未知的打包模式: {mode}", "ERROR")
                self.root.after(0, self.reset_ui)
                return
            
            script_path = SCRIPT_DIR / script_name
            
            # 创建清理脚本（如果不存在）
            if mode == "clean" and not script_path.exists():
                self.create_clean_script()
            
            # 执行脚本
            self.current_process = subprocess.Popen(
                [str(script_path)],
                cwd=str(SCRIPT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 读取输出并获取返回码
            return_code = None
            while True:
                output = self.current_process.stdout.readline()
                if output == '' and self.current_process.poll() is not None:
                    return_code = self.current_process.poll()  # 在进程结束时获取返回码
                    break
                if output and output.strip():  # 确保输出不为空
                    self.root.after(0, lambda msg=output.strip(): self.log_message(msg))
            
            # 使用已经获取的返回码
            if return_code == 0:
                self.log_message(f"进程正常结束，返回码: {return_code}", "SUCCESS")
                self.root.after(0, lambda: self.on_packaging_success(mode))
            else:
                self.log_message(f"进程异常结束，返回码: {return_code}", "ERROR")
                self.root.after(0, lambda: self.on_packaging_failed(mode, return_code))
                
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"打包过程出错: {e}", "ERROR"))
            self.root.after(0, self.reset_ui)
    
    def create_clean_script(self):
        """创建清理脚本"""
        clean_script = SCRIPT_DIR / "clean_temp_files.sh"
        clean_content = f'''#!/bin/bash
# 清理临时文件脚本

set -e

echo "开始清理临时文件..."

# 清理构建缓存
if [ -d "{PROJECT_ROOT.parent}/build" ]; then
    echo "删除构建缓存..."
    rm -rf "{PROJECT_ROOT.parent}/build"/*
    echo "构建缓存清理完成"
fi

# 清理临时目录
if [ -d "{PROJECT_ROOT}/temp" ]; then
    echo "删除临时目录..."
    rm -rf "{PROJECT_ROOT}/temp"/*
    echo "临时目录清理完成"
fi

# 清理PyInstaller缓存
echo "清理PyInstaller缓存..."
rm -rf ~/.cache/pyinstaller/* 2>/dev/null || true

echo "所有临时文件清理完成"
'''
        
        with open(clean_script, 'w', encoding='utf-8') as f:
            f.write(clean_content)
        
        clean_script.chmod(0o755)
        self.log_message(f"创建清理脚本: {clean_script}")
    
    def on_packaging_success(self, mode):
        """打包成功"""
        self.progress_bar.stop()
        self.progress_var.set(f"{self.get_mode_name(mode)}完成")
        self.log_message(f"{self.get_mode_name(mode)}成功完成！", "SUCCESS")
        
        # 如果是构建模式，显示文件信息
        if mode in ["quick", "appimage"]:
            self.show_build_results(mode)
        
        self.reset_ui()
    
    def on_packaging_failed(self, mode, return_code):
        """打包失败"""
        self.progress_bar.stop()
        self.progress_var.set(f"{self.get_mode_name(mode)}失败")
        self.log_message(f"{self.get_mode_name(mode)}失败，返回码: {return_code}", "ERROR")
        self.reset_ui()
    
    def show_build_results(self, mode):
        """显示构建结果"""
        try:
            if mode == "quick":
                executable = DISH_DIR / "NetEaseCloudMusic"
                if executable.exists():
                    size = executable.stat().st_size / (1024 * 1024)  # MB
                    self.log_message(f"可执行文件: {executable} ({size:.1f}MB)", "SUCCESS")
            
            elif mode == "appimage":
                appimage_files = list(DISH_DIR.glob("*.AppImage"))
                if appimage_files:
                    for appimage in appimage_files:
                        size = appimage.stat().st_size / (1024 * 1024)  # MB
                        self.log_message(f"AppImage文件: {appimage.name} ({size:.1f}MB)", "SUCCESS")
                        
        except Exception as e:
            self.log_message(f"获取构建结果失败: {e}", "ERROR")
    
    def reset_ui(self):
        """重置UI状态"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_var.set("就绪")
        self.current_process = None
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def open_output_dir(self):
        """打开输出目录"""
        try:
            if DISH_DIR.exists():
                if sys.platform == "linux":
                    subprocess.run(["xdg-open", str(DISH_DIR)], check=False)
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", str(DISH_DIR)], check=False)
                elif sys.platform == "win32":  # Windows
                    subprocess.run(["explorer", str(DISH_DIR)], check=False)
                else:
                    messagebox.showinfo("输出目录", f"输出目录: {DISH_DIR}")
            else:
                messagebox.showwarning("警告", "输出目录不存在")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开输出目录: {e}")
    
    def get_mode_name(self, mode):
        """获取模式的中文名称"""
        names = {
            "quick": "快速构建",
            "appimage": "AppImage构建",
            "check": "依赖检查", 
            "test": "测试",
            "clean": "清理"
        }
        return names.get(mode, mode)

def main():
    """主函数"""
    root = tk.Tk()
    app = PackagingGUI(root)
    
    # 处理窗口关闭事件
    def on_closing():
        if app.current_process and app.current_process.poll() is None:
            if messagebox.askyesno("确认", "打包正在进行中，确定要退出吗？"):
                app.stop_packaging()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 启动GUI
    root.mainloop()

if __name__ == "__main__":
    main()
