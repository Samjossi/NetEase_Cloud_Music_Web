#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单一托盘集成测试
验证重复托盘问题已解决
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel, QTextEdit
from PySide6.QtCore import QTimer

# 导入我们的模块
from logger import init_logging, get_logger
from gui.main_window import NetEaseMusicWindow


class SingleTrayTestWindow(QWidget):
    """单一托盘集成测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("single_tray_test")
        self.init_ui()
        self.test_single_tray()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("单一托盘集成测试")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("正在测试单一托盘集成...")
        layout.addWidget(self.status_label)
        
        # 测试结果区域
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        # 测试按钮
        self.test_btn = QPushButton("重新测试")
        self.test_btn.clicked.connect(self.test_single_tray)
        layout.addWidget(self.test_btn)
        
        self.setLayout(layout)
        
    def log_result(self, message: str, success: bool = True):
        """添加测试结果"""
        timestamp = time.strftime("%H:%M:%S")
        status = "✅" if success else "❌"
        self.results_text.append(f"[{timestamp}] {status} {message}")
        self.logger.info(message)
        
    def test_single_tray(self):
        """测试单一托盘集成"""
        self.results_text.clear()
        self.log_result("开始单一托盘集成测试...")
        
        try:
            # 创建主窗口（这会初始化托盘）
            self.main_window = NetEaseMusicWindow()
            
            # 检查托盘管理器
            if hasattr(self.main_window, 'tray_manager') and self.main_window.tray_manager:
                self.log_result("✓ 主窗口包含托盘管理器")
                
                # 检查托盘是否可见
                if self.main_window.tray_manager.is_visible:
                    self.log_result("✓ 托盘管理器可见")
                else:
                    self.log_result("⚠ 托盘管理器不可见", False)
                
                # 检查PipeWire集成
                if hasattr(self.main_window, 'pipewire_integration') and self.main_window.pipewire_integration:
                    self.log_result("✓ PipeWire集成存在")
                    
                    # 检查PipeWire管理器
                    if hasattr(self.main_window.pipewire_integration, 'pipewire_manager'):
                        self.log_result("✓ PipeWire管理器已集成")
                    else:
                        self.log_result("❌ PipeWire管理器未集成", False)
                else:
                    self.log_result("❌ PipeWire集成不存在", False)
                
                # 检查通知连接
                if (hasattr(self.main_window, 'pipewire_integration') and 
                    self.main_window.pipewire_integration and
                    hasattr(self.main_window.pipewire_integration, 'restart_notification_requested')):
                    self.log_result("✓ PipeWire通知信号已定义")
                else:
                    self.log_result("❌ PipeWire通知信号未定义", False)
                
            else:
                self.log_result("❌ 主窗口缺少托盘管理器", False)
            
            # 测试托盘功能
            self._test_tray_functionality()
            
            self.status_label.setText("单一托盘集成测试完成")
            
        except Exception as e:
            self.log_result(f"测试失败: {e}", False)
            self.status_label.setText("测试失败")
    
    def _test_tray_functionality(self):
        """测试托盘功能"""
        try:
            # 检查托盘图标
            if hasattr(self.main_window.tray_manager, 'qt_tray'):
                tray = self.main_window.tray_manager.qt_tray
                if tray and hasattr(tray, 'isVisible'):
                    if tray.isVisible():
                        self.log_result("✓ 托盘图标可见")
                    else:
                        self.log_result("⚠ 托盘图标不可见", False)
                else:
                    self.log_result("❌ 托盘对象无效", False)
            else:
                self.log_result("❌ 托盘对象不存在", False)
            
            # 检查托盘菜单
            if hasattr(self.main_window.tray_manager, 'qt_tray'):
                tray = self.main_window.tray_manager.qt_tray
                if hasattr(tray, 'contextMenu'):
                    menu = tray.contextMenu()
                    if menu and menu.actions():
                        self.log_result(f"✓ 托盘菜单包含 {len(menu.actions())} 个选项")
                    else:
                        self.log_result("❌ 托盘菜单为空", False)
                else:
                    self.log_result("❌ 托盘菜单不存在", False)
            
            # 检查PipeWire配置
            from profile_manager import get_profile_manager
            profile_manager = get_profile_manager()
            config = profile_manager.get_pipewire_full_config()
            
            if config:
                self.log_result(f"✓ PipeWire配置加载成功: {len(config)} 个配置项")
                
                if config.get('auto_restart_enabled'):
                    self.log_result("✓ PipeWire自动重启已启用")
                else:
                    self.log_result("⚠ PipeWire自动重启未启用")
                
                if config.get('restart_interval_songs'):
                    interval = config.get('restart_interval_songs')
                    self.log_result(f"✓ 重启间隔: {interval}首歌")
                else:
                    self.log_result("❌ 重启间隔未设置", False)
            else:
                self.log_result("❌ PipeWire配置加载失败", False)
                
        except Exception as e:
            self.log_result(f"托盘功能测试失败: {e}", False)


def main():
    """主函数"""
    # 初始化日志系统
    logger_manager = init_logging(
        level="INFO",
        console_output=True,
        file_output=False,
        json_output=False
    )
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = SingleTrayTestWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
