# Markdown 阅览模式渲染内核复现指南（markdown-it-py 方案）

> **定位**：跨项目复现教程。面向需要在自己的 Python/PySide6 软件中改进
> Markdown **阅览模式** 渲染质量的工程师，照做即可得到与 Zen_Studio
> 2026-0811-0402 计划同款的改造效果。
> **产出蓝本**：Zen_Studio 仓库 `文档/修改记录/2026-0811-0402_Markdown阅览
> 模式渲染内核替换markdown-it计划.md`（含实施记录 §八，可对照查阅）。
> **时间**：2026-08-11 04:34（UTC+8）

---

## 一、你将得到什么

把 Qt 内建 `QTextDocument.setMarkdown()` 替换为 **markdown-it-py**
（CommonMark 官方参考实现的 Python 移植版，MIT 许可）渲染内核：

| 维度 | 改造前（Qt setMarkdown） | 改造后（markdown-it-py） |
|---|---|---|
| GFM 支持 | 不完整：复杂表格/任务列表粗糙 | CommonMark 全量 + 表格 + 删除线（gfm-like 预设） |
| 任务列表 | `- [ ]` 显示为原文或乱码方框 | 渲染为着色的 ☑ / ☐ |
| 样式可控性 | 弱（标题阶梯/代码块排版受内建转换器制约） | 样式表全自控：标题字号阶梯、表头底色、代码块底块、引用边线 |
| 相对图片 | 依实现而定 | loadResource 机制照常工作 |
| 依赖 | 零（Qt 内建） | 两个 vendor 包（MIT、纯 Python，< 0.5MB） |

**总原则：保持轻型简洁。** 不引插件生态（mdit-py-plugins）、不做代码块
语法着色（不引 Pygments）、不启用裸 URL 自动链接（linkify）、不做主题
切换重渲染。这些是踩过坑后的刻意取舍，复现时请原样遵循，勿擅自加料。

---

## 二、前置条件

- 技术栈：Python 3.10+ / PySide6（PyQt6 亦可，API 同名）。
- 你的阅览控件是 `QTextBrowser`（或 `QTextEdit` 只读）子类，当前用
  `setMarkdown()` 或类似方式渲染。
- 项目根目录在 `sys.path` 中（即 `python main.py` 启动时项目根可 import）。
- 能跑离屏测试（`QT_QPA_PLATFORM=offscreen`）做冒烟验证。

---

## 三、依赖路线：源码 vendor 融合（不经 pip/uv）

**关键决策：不通过 pip/uv 安装，直接把包源码拷进项目。** 理由：

1. `pyproject.toml` / 锁文件零改动，不污染依赖声明；
2. PyInstaller 打包按 import 链自动收编，无需 hidden-import 配置；
3. import 形态与 pip 安装**完全一致**（`from markdown_it import MarkdownIt`），
   未来若想切回正规依赖管理，消费代码一行不用改。

### 3.1 获取源码

```bash
# 备份快照（供溯源与日后升级重拷）
git clone --depth 1 https://github.com/executablebooks/markdown-it-py 参考代码/markdown-it-py-master
git clone --depth 1 https://github.com/executablebooks/mdurl 参考代码/mdurl-master
```

> `mdurl` 是 markdown-it-py 的**唯一运行依赖**（链接 URL 规范化用），
> 必须一并 vendor，缺一不可。

### 3.2 拷贝包目录到项目根（附 LICENSE，协议合规）

```bash
# markdown-it-py：包目录在仓库根的 markdown_it/
cp -r 参考代码/markdown-it-py-master/markdown_it ./markdown_it
cp 参考代码/markdown-it-py-master/LICENSE ./markdown_it/LICENSE
cp 参考代码/markdown-it-py-master/LICENSE.markdown-it ./markdown_it/LICENSE.markdown-it

# mdurl：包目录在 src/ 下
cp -r 参考代码/mdurl-master/src/mdurl ./mdurl
cp 参考代码/mdurl-master/LICENSE ./mdurl/LICENSE
```

只拷纯包目录，不带上游 tests/docs/benchmarking。两包均 MIT 许可，
LICENSE 随包即合规。

### 3.3 import 冒烟

```bash
python -c "
from markdown_it import MarkdownIt
md = MarkdownIt('gfm-like').disable('linkify')   # ← 注意：必须 disable，见坑 1
print(md.render('# 标题\n\n- [x] 任务\n'))
"
```

预期输出含 `<h1>标题</h1>`。看到这行就说明 vendor 成功。

---

## 四、核心改造（三处代码）

假设你的阅览控件大致是这样一个 `QTextBrowser` 子类（以下以此形态讲解，
请映射到自己的类）：

```python
class MarkdownView(QTextBrowser):
    def open_markdown(self, path: Path) -> str | None:
        text = path.read_bytes().decode("utf-8")
        self.document().setMarkdown(text, ...)   # ← 旧路径，将被替换
```

### 4.1 渲染器装配 + 任务列表规则（新代码，约 40 行）

把下面这段原样放进你的阅览控件模块（或独立的 renderer 模块）：

```python
import re

from markdown_it import MarkdownIt
from markdown_it.token import Token   # ← 注意：从这里导入，见坑 2

#: GFM 任务列表标记：列表项行内文本开头的 [ ] / [x]（大小写兼容）
_TASK_MARK_RE = re.compile(r"^\[([ xX])\]\s+")


def _task_list_check_rule(state) -> bool:
    """core ruler 极简规则：列表项开头的 [ ]/[x] 渲染为 Unicode ☐/☑。

    不引 mdit-py-plugins（保持轻型）：QTextBrowser 不支持 <input> 复选框，
    Unicode 字符是唯一轻量可行形态；边角形态（如标记后多个空格）降级为
    原文显示 [ ]，可接受。
    """
    in_item = False
    for token in state.tokens:
        if token.type == "list_item_open":
            in_item = True
        elif token.type == "list_item_close":
            in_item = False
        elif in_item and token.type == "inline" and token.children:
            first = token.children[0]
            if first.type != "text":
                continue
            m = _TASK_MARK_RE.match(first.content)
            if not m:
                continue
            first.content = first.content[m.end():]          # 剥掉 [ ] 原文
            check = Token("html_inline", "", 0)
            symbol = "☑" if m.group(1).lower() == "x" else "☐"
            check.content = f'<span class="task-check">{symbol}</span> '
            token.children.insert(0, check)
    return False


def _build_renderer() -> MarkdownIt:
    """装配渲染内核：gfm-like 预设（CommonMark 全量 + 表格 + 删除线），
    linkify 禁用（免 linkify-it-py/uc-micro-py 第二依赖链），
    追加任务列表 ☑/☐ 规则。"""
    md = MarkdownIt("gfm-like").disable("linkify")
    md.core.ruler.push("task_list_check", _task_list_check_rule)
    return md
```

在控件 `__init__` 里持有一份实例（渲染器可复用，不要每次渲染新建）：

```python
self._renderer = _build_renderer()
```

### 4.2 打开与渲染（替换旧路径）

```python
def open_markdown(self, path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError as e:
        return str(e)
    # —— 大文件截断守卫（建议保留你原有的；参考值 1MB）——
    self._truncated = len(raw) > 1_048_576
    if self._truncated:
        raw = raw[:1_048_576]
    try:
        # 截断可能切断 UTF-8 多字节字符：截断场景宽容解码，未截断严格解码
        text = raw.decode("utf-8", errors="ignore" if self._truncated else "strict")
    except UnicodeDecodeError:
        return "编码非 UTF-8，不支持渲染预览"

    # 相对图片/链接解析基准（保留你原有的外围机制，这部分不变）
    self.setSearchPaths([str(path.parent)])
    self.document().setBaseUrl(QUrl.fromLocalFile(str(path.parent) + "/"))

    # ★ 核心替换：setMarkdown → markdown-it-py 渲染 + setHtml
    # setHtml 同样走 loadResource + searchPaths + baseUrl，相对图片解析不变
    self.setHtml(self._renderer.render(text))
    return None
```

**对外接口保持不变**（方法名、返回值、信号全不动），调用方（面板/标签页）
零改动——这是本方案的重要约束，请同样遵守。

### 4.3 样式表（Qt 富文本 CSS 子集内适度排版）

markdown-it-py 输出的是干净 HTML，排版观感由 `QTextDocument` 的默认样式表
决定。在主题切换处重建样式表（色值从你自己的主题令牌取，勿硬编码）：

```python
def _build_stylesheet(palette: dict) -> str:
    text = palette["text"]
    muted = palette["muted_text"]
    accent = palette["accent"]
    border = palette["border"]
    code_bg = palette["chrome"]["line_number_bg"]   # 借用一个现有底色令牌
    return f"""
        body {{ color: {text}; }}
        a {{ color: {accent}; text-decoration: none; }}
        h1 {{ font-size: xx-large; }}
        h2 {{ font-size: x-large; }}
        h3 {{ font-size: large; }}
        code, pre {{ background-color: {code_bg}; }}
        pre {{ padding: 8px; }}
        pre code {{ background-color: transparent; }}
        blockquote {{
            color: {muted};
            margin-left: 16px;
            border-left: 3px solid {border};
            padding-left: 8px;
        }}
        table td, table th {{ border: 1px solid {border}; padding: 4px 8px; }}
        table th {{ background-color: {code_bg}; }}
        hr {{ color: {border}; background-color: {border}; }}
        .task-check {{ color: {accent}; }}
    """

def apply_theme(self, palette: dict) -> None:
    self.document().setDefaultStyleSheet(self._build_stylesheet(palette))
    self.viewport().update()
```

要点：

- 标题字号用**相对关键字**（xx-large/x-large/large），自动跟随全局字号
  缩放，不做动态 pt 计算；
- 因为没有内联色，**主题切换只需换样式表，无需重渲染**——这是「不做
  代码块语法着色」换来的红利，请守住；
- `.task-check` 选择器对应 4.1 规则里 span 的 class，负责 ☑/☐ 着色。

---

## 五、踩坑记录（务必逐项核对）

这四条都是 Zen_Studio 实施时实测踩出来的，照抄代码也会踩，提前知晓：

### 坑 1：gfm-like 预设默认启用 linkify，缺包即崩

`MarkdownIt("gfm-like")` 渲染第一篇文档就会抛
`ModuleNotFoundError: Linkify enabled but not installed.`——gfm-like
预设把 linkify 规则打开了，而它依赖 linkify-it-py + uc-micro-py
第二依赖链。**对策**：`.disable("linkify")`（代价：裸 URL 文本不自动
变链接，写成 `[文字](url)` 的链接不受影响，可接受）。

### 坑 2：`state.Token` 不存在

core 规则里创建 Token 不能用 `state.Token(...)`（StateCore 没有这个
属性，会报 AttributeError）。**对策**：`from markdown_it.token import Token`，
直接 `Token("html_inline", "", 0)`。

### 坑 3：Qt `toHtml()` 会规范化标签，自动化断言别拿它查标签

markdown-it-py 输出的 `<s>删除</s>`，经 Qt 加载后再 `toHtml()` 导出，
会变成 `<span style="text-decoration: line-through;">`；`<h1>` 也会变成
带 style 的 span。**对策**：自动化测试用**双层断言口径**——
内核原始输出 `md.render(text)` 查标签结构（`<h1`/`<table`/`<s>`），
Qt 文档 `toHtml()` 查可视语义（"☑" 存在、"[ ]" 不存在、
"line-through" 存在）。

### 坑 4：`loadResource` 是 C++ 虚函数，猴子补丁拦不到

想在探针里验证相对图片确实命中了资源加载，patch
`QTextDocument.loadResource` 是无效的。**对策**：探针侧定义子类覆写：

```python
class SpyView(MarkdownView):
    def loadResource(self, rtype, url):
        loaded.append((rtype, url.toString()))
        return super().loadResource(rtype, url)
```

---

## 六、验证清单（照此验收，勿凭肉眼交付）

### 6.1 离屏冒烟探针（自动化断言）

`QT_QPA_PLATFORM=offscreen python probe_md_it.py`，断言四项：

1. **渲染断言**：样例 md（标题阶梯/表格/任务列表/围栏代码块/删除线/
   相对图片/链接）渲染后——内核原始 HTML 含 `<h1>/<table>/<s>`，
   ☑/☐ 出现且 `[ ]`/`[x]` 原文不残留（用坑 3 的双层口径）；
2. **相对图片回归**：loadResource 子类拦截（坑 4），确认图片 URL 命中；
3. **链接分发回归**：http→系统浏览器、工作区文件→你的文件打开信号、
   `#锚点`→页内跳转，各点一遍；
4. **截断守卫 + 计时**：构造 >1MB 的 md，确认截断生效、渲染耗时在
   1s 级（断言上限建议放宽到 2s，防机器差异脆断）。

### 6.2 视觉验证（截图前后对照）

逻辑断言 ≠ 像素可见。用 `widget.grab().save(path)` 截三张图人工核对：

- **before**：旧 setMarkdown 路径渲染同一份样例（探针里临时调用即可，
  生产代码不残留旧路径）；
- **after**：新内核渲染，核对——标题阶梯分明、表格有边框和表头底色、
  代码块整宽底块、☑/☐ 着色、相对图片真实显示（改造前常见破图图标）；
- **第二主题 after**：换一套主题重截，确认色值全部从令牌派生、无硬编码色。

### 6.3 既有功能回归

如果你的阅览页还有其他机制（源码/阅览切换、查找浮层、右键菜单等），
把对应的既有探针复跑一遍。本方案对外接口零变化，回归应当全绿。

---

## 七、验收标准（Definition of Done）

- [ ] `markdown_it/` + `mdurl/` 在项目根，LICENSE 随包，import 冒烟通过；
- [ ] `_build_renderer()` 装配 gfm-like + 禁 linkify + 任务列表规则；
- [ ] `open_markdown()` 走 `md.render()` + `setHtml()`，对外接口签名不变；
- [ ] 样式表扩展落地，色值全部主题令牌派生；
- [ ] 冒烟探针四项全绿 + 既有回归全绿；
- [ ] 前后对照截图人工核对通过；
- [ ] pyproject/锁文件零改动；
- [ ] 模块 docstring 注明本次改造来源（便于后人溯源）。

---

## 八、不做的事（刻意取舍，勿加回来）

| 不做 | 原因 |
|---|---|
| 代码块语法着色（Pygments） | 引入内联色 → 主题切换必须重渲染全文，复杂度陡增；单色底块观感已够用 |
| mdit-py-plugins（脚注/锚点/front matter） | 低频需求；YAML 头按普通文本显示可接受 |
| linkify 裸 URL 自动链接 | 免第二依赖链（坑 1）；显式 `[文字](url)` 链接不受影响 |
| 主题切换重渲染 | 无内联色需求，换样式表即可，渲染路径零改动 |
| QWebEngine / JS 移植 | 重型方案，与本「轻型简洁」路线相悖 |

## 九、升级与维护

vendor 快照与上游脱钩，后续升级靠**人工重拷**：重新 clone 上游 → 重复
§3.2 拷贝 → 复跑 §6 验证清单。上游 commit 号记录在备份快照里可查溯源。
markdown-it-py 与 JS 版 API/插件架构一一对应，遇行为疑问直接查
JS markdown-it 文档同样有效。
