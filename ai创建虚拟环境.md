### 1.创建虚拟环境

```bash
# 使用 Python 3.12 创建
uv venv .venv --python 3.12
```

### 2.激活虚拟环境

```bash
# Linux / macOS
source .venv/bin/activate
```



**注意**：必须先 `cd` 进入项目目录，初始化后方能安装依赖包。

```bash
# 初始化项目（生成 pyproject.toml）
uv init
```

### 3.安装依赖

```bash
# 安装单个包（自动写入 pyproject.toml）
uv add 依赖包名

# 从 requirements.txt 安装（根目录）
uv pip install -r requirements.txt

# 批量安装（指定环境路径）
uv add -r ~/env_环境名/requirements.txt

# 常规 pip 安装（不推荐，优先用 uv add）
uv pip install requests
```

### 4.新建常用命令文档
```bash
在根目录新建一个“常用命令.md”文档，里面内容很简洁，就单纯的用uv run运行当前入口的命令```
```