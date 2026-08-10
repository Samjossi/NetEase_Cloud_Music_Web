# Linux 桌面关机优雅退出通用技术方案

> **状态**：已确认
> **范围**：通用技术指引（面向工程师，可应用于任意桌面软件）
> **时间**：2026-07-29 16:26（设计，UTC+8）
> **优先级**：中

---

## 1. 要解决的问题

Linux 桌面（GNOME/systemd 环境）关机时，系统对「资源拆除」与「进程终止」
**不做严格排序**：FUSE 挂载、D-Bus 总线、显示服务器等基础设施可能与业务
进程同时被 teardown。进程若在资源消失后仍访问它，即产生崩溃：

| 场景 | 崩溃形态 |
|:---|:---|
| AppImage / 自挂载运行时（FUSE 先拆，进程仍在取指令页） | SIGBUS（信号 7） |
| 显示连接（X11/Wayland）先断，GUI 线程仍在绘制 | SIGSEGV（信号 11） |
| D-Bus 会话总线先断，进程仍持有代理调用 | 异常退出 / 断言失败 |

崩溃转储被 Apport 等系统收集器捕获后，用户下次登录会看到
「检测到系统程序出现问题」弹窗——**对软件本身无害，但严重损害用户信任**。

**核心结论：只要进程在关机流程到达「资源拆除」阶段之前自行退出，
所有此类崩溃均可避免。** 本方案提供三层检测点，按可靠性从高到低叠加使用。

---

## 2. 关机时序与检测点

```text
用户点击「关机」
  → gnome-shell 弹出确认对话框（约 60 秒倒计时）
  → gnome-session 向已注册客户端广播 QueryEndSession（询问）
        │
用户确认 / 倒计时结束
  → gnome-session 广播 EndSession          ←【检测点 ①：最早，应用应在此退出】
  → systemd-logind 广播 PrepareForShutdown ←【检测点 ②：兜底】
  → systemd 停止用户单元、拆 FUSE、断总线   ←【崩溃发生区：进程必须已退出】
  → 内核关机 / 重启
```

时序要点：

- 检测点 ① 触发时，会话总线仍存活，距资源拆除尚有数秒，**从容退出完全够用**
- 切勿在 QueryEndSession 阶段（倒计时刚弹出）退出——用户可能点「取消」，
  提前退出会导致应用无故消失
- 检测点 ② 触发时关机已不可撤销，仍早于资源拆除，作为最后保险

---

## 3. 各技术栈接入方法

### 3.1 Qt 应用（C++ / PySide6 / PyQt6）—— 检测点 ①

Qt6 的 xcb 平台插件会自动向 GNOME SessionManager 注册客户端，
收到 EndSession 后发射 `commitDataRequest`。只需连接该信号：

```python
# main.py（PySide6 示例）
def _setup_graceful_session_exit(app: QApplication) -> None:
    """会话结束（关机/注销确认后）立即自行退出。"""
    app.commitDataRequest.connect(lambda _session: app.quit())
```

```cpp
// main.cpp（Qt C++ 示例）
QObject::connect(&app, &QGuiApplication::commitDataRequest,
                 &app, [](QSessionManager &) { QCoreApplication::quit(); });
```

约束（🔴 必须遵守）：

- 处理函数内**禁止弹窗、禁止交互、禁止阻塞**；不调用 `session.cancel()`
- 清理动作（断监听、关句柄）挂在 `aboutToQuit` 上，随 `quit()` 自动触发
- 数据持久化应平时即时提交，不要把「退出时统一保存」作为前提

### 3.2 GTK 应用（C / Python）—— 检测点 ①

GTK 无内建会话客户端封装，直接向 GNOME SessionManager 注册：

```python
# session_exit.py（PyGObject 示例）
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

def register_session_client(app_id: str, on_end_session) -> None:
    """注册为 GNOME 会话客户端，收到 EndSession 时回调 on_end_session。"""
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    # 1. 注册客户端，拿到对象路径
    result = bus.call_sync(
        "org.gnome.SessionManager",
        "/org/gnome/SessionManager",
        "org.gnome.SessionManager",
        "RegisterClient",
        GLib.Variant("(ss)", (app_id, "")),
        GLib.VariantType("(o)"),
        Gio.DBusCallFlags.NONE, -1, None,
    )
    client_path = result.unpack()[0]

    # 2. 监听该客户端对象的 EndSession 信号
    def _on_signal(_conn, _sender, _path, _iface, signal, _params):
        if signal == "EndSession":
            on_end_session()   # 例如 GLib.idle_add(Gtk.main_quit)

    bus.signal_subscribe(
        "org.gnome.SessionManager",
        "org.gnome.SessionManager.ClientPrivate",
        None, client_path, None,
        Gio.DBusSignalFlags.NONE, _on_signal,
    )
```

同时需响应 `QueryEndSession` 并调用 `EndSessionResponse(true, "")`，
否则会阻止关机流程（完整实现参考 GNOME SessionManager D-Bus API 文档）。

### 3.3 任意语言 —— 检测点 ②（logind，通用兜底）

logind 的 `PrepareForShutdown` 是系统总线信号，任何进程都能订阅，
**不依赖桌面环境，GNOME/KDE/Wayland 均有效**：

```python
# logind_watch.py（通用示例，依赖 dbus-next 或 QtDBus 等任意 D-Bus 库）
from dbus_next.aio import MessageBus
import asyncio

async def watch_shutdown(on_shutdown) -> None:
    """监听 logind 关机广播，触发 on_shutdown 回调。"""
    bus = await MessageBus().connect()
    bus.add_match_rule(
        "type='signal',"
        "sender='org.freedesktop.login1',"
        "interface='org.freedesktop.login1.Manager',"
        "member='PrepareForShutdown'"
    )
    # 在消息循环中收到该信号后调用 on_shutdown()（应触发主程序退出）
```

shell 侧等价验证命令（无需写代码即可观察该信号）：

```bash
# 终端执行：实时监控关机广播（Ctrl+C 停止）
dbus-monitor --system "type='signal',interface='org.freedesktop.login1.Manager',member='PrepareForShutdown'"
```

### 3.4 系统侧兜底 —— systemd 单元（零代码方案）

对无法修改源码的软件，用 systemd 用户单元在关机前代为终止：

```ini
# ~/.config/systemd/user/<app>-shutdown.service
[Unit]
Description=Gracefully quit <app> before shutdown
Before=graphical-session.target

[Service]
Type=oneshot
ExecStart=/bin/true
ExecStop=/usr/bin/pkill -TERM -f <进程匹配模式>
RemainAfterExit=yes

[Install]
WantedBy=graphical-session.target
```

```bash
# 启用命令
systemctl --user daemon-reload
systemctl --user enable <app>-shutdown.service
```

---

## 4. 实施准则（各层通用）

| 准则 | 说明 |
|:---|:---|
| 🔴 快速退出 | 从收到信号到进程结束目标 < 1 秒；只做内存级清理，不做网络请求、大数据写盘 |
| 🔴 禁止交互 | 关机信号处理中不得弹任何对话框（"是否保存？"类交互会把应用挂住，反而被强拆） |
| 🔴 平时即时持久化 | 数据安全依赖「写入即提交」，而非「退出时保存」 |
| 🟡 静默降级 | 无会话总线 / 无系统总线（headless、CI、容器）时连接失败必须静默跳过，不得影响正常启动 |
| 🟡 分层叠加 | ① 会话信号为主，② logind 兜底，③ systemd 单元仅用于不可改码的软件 |
| 🟢 幂等清理 | 退出路径可被 SIGTERM 与信号触发多次，清理逻辑需幂等 |

## 5. 验证方法

| 验证项 | 方法 | 通过标准 |
|:---|:---|:---|
| 真实关机 | 保持应用运行，直接重启系统 | 无新崩溃转储（Ubuntu: `/var/crash/` 无新增）；`journalctl -b -1` 中应用进程在 logind reboot 记录前已退出 |
| 会话信号模拟 | `gdbus emit --session --object-path <client_path> --signal org.gnome.SessionManager.ClientPrivate.EndSession`（先注册拿到路径） | 进程 1 秒内退出 |
| logind 信号观察 | §3.3 的 `dbus-monitor` 命令挂后台后发起关机（随后取消） | 能看到信号输出 |
| 无总线环境 | offscreen / headless 启动 | 正常启动无报错 |

## 6. 适用范围与限制

| 环境 | ① GNOME 会话信号 | ② logind 信号 | ③ systemd 单元 |
|:---|:---:|:---:|:---:|
| GNOME + X11 | ✅ | ✅ | ✅ |
| GNOME + Wayland | ⚠️ Qt 依赖平台插件实现，GTK 自注册可用 | ✅ | ✅ |
| KDE Plasma | ⚠️ 需改用 KSMServer 协议（Qt 自动处理） | ✅ | ✅ |
| 无桌面（服务器） | ❌ | ✅（需 systemd-logind 运行） | ✅ |
| 容器 / CI | ❌ | ❌ | ❌（也无需处理） |

---

*方案整理：2026-07-29 16:26 (UTC+8) | 源自本项目 `2026-0729-0915_系统崩溃弹窗排查报告.md` 的排查结论与 `2026-0729-1610_关机时commitDataRequest优雅退出实施计划.md` 的工程实践*
