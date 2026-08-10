# Dear PyGui 项目启动规范

## 必须项

### 1. 主循环加帧率限制

每帧渲染后必须 `sleep`，限制帧率，防止 CPU 空转吃满。

- **要求**：必须存在 `time.sleep(1 / target_fps)`。
- **target_fps**：由项目需求决定，**不可**写死为某个固定值；应在项目配置或启动参数中定义。

Python

 

```python
import time
# target_fps 应从项目配置读取，例如 config.get("target_fps", 60)
while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()
    time.sleep(1 / target_fps)
```

------

### 2. 单实例锁

启动时绑定本地端口，若已被占用则直接退出，防止重复启动多个实例。

- **要求**：必须存在单实例锁机制。
- **端口号**：**不可**硬编码为固定值（如 `65432`）；必须从项目配置、环境变量或自动分配逻辑中获取，确保**每个独立项目使用不同端口**。

Python

 

```python
import socket
# lock_port 应从项目配置或环境变量读取，例如 int(os.getenv("APP_LOCK_PORT", 0))
# 若未指定，建议按项目名哈希生成或报错要求显式配置
try:
    _lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _lock.bind(("127.0.0.1", lock_port))
except socket.error:
    print(f"实例已在运行（端口 {lock_port} 被占用）")
    exit(1)
```

------

## 规则

1. **以上两项机制必须同时存在**，缺一不可。
2. **具体数值（target_fps、lock_port）必须由项目上下文决定**，禁止在代码中写死。
3. 若 AI 生成代码时发现配置未提供，**应显式声明占位符**并提示用户补充，而非擅自填入默认值。

------
