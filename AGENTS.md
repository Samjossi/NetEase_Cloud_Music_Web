AGENTS

- 仅操作项目目录内文件，禁止访问外部路径
- 强制使用项目 `.venv` 的 Python，禁止系统全局 Python
- 如需生成临时文件、缓存或测试数据，必须存放在项目根目录内（如 `./.temp/`、`./tmp/` 或 `./cache/`），严禁使用系统临时目录（如 `/tmp`、`/var/tmp`、`C:\Windows\Temp`、`$TMPDIR` 等）
- 有时候使用绝对路径的时候就会被系统认为是目录外的文件而被要求权限，这个时候就尝试一下相对路径
- Always think and respond in Chinese (中文). 所有思考过程和输出必须使用中文。
- commit message 使用中文