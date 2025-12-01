# PipeWire配置说明

## 配置文件位置

PipeWire配置存储在用户数据目录：
```
~/.local/share/netease-music/login_data/pipewire_config.json
```

## 基础配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `auto_restart_enabled` | 布尔值 | `true` | 是否启用自动重启功能 |
| `restart_interval_songs` | 字符串 | `"16"` | 播放多少首歌后重启 |
| `show_notifications` | 布尔值 | `true` | 是否显示重启通知 |
| `restart_command` | 字符串 | `"systemctl --user restart pipewire"` | 重启命令 |

## 默认配置

```json
{
    "auto_restart_enabled": true,
    "restart_interval_songs": "16",
    "show_notifications": true,
    "restart_command": "systemctl --user restart pipewire"
}
```

## 功能说明

### 自动重启机制
- 系统在播放16首歌后自动重启PipeWire服务
- 优先在歌曲切换间隙或暂停时重启
- 避免中断音乐播放

### 重启时机
- **唯一时机**：播放16首歌后，在切换到第17首歌曲的间隙（5秒内）执行
- 简单直接，避免复杂判断

### 通知系统
- 重启开始时显示通知
- 重启完成时显示结果
- 可通过配置关闭通知

## 配置修改

### 通过托盘菜单
1. 右键点击系统托盘图标
2. 选择"PipeWire配置"
3. 查看当前配置状态

### 手动编辑
直接编辑配置文件 `pipewire_config.json`

## 故障排除

### 重启失败
- 检查用户权限：`systemctl --user status pipewire`
- 确认PipeWire服务运行：`systemctl --user is-active pipewire`

### 配置重置
删除配置文件即可恢复默认设置：
```bash
rm ~/.local/share/netease-music/login_data/pipewire_config.json
