# AI 友好代码协议
# AI-Friendly Code Protocol (AFCP)

> **版本**: v1.2.0
> **日期**: 2026-07-05
> **适用场景**: 所有由 AI 生成、维护或协作编写的代码项目（不限语言、不限范式）

---

## 核心原则

AI 友好代码协议的核心只有一句话：

> **让代码的"文本表面"承载尽量多的意图信息。**

人类开发者拥有视觉直觉、项目背景和业务上下文，而 AI 只能依赖纯文本推理。因此，代码中的每一个名字、每一种结构、每一处注释，都必须成为 AI 理解系统的**显式线索**，而非需要猜测的隐式约定。

---

## 一、命名规则：名字本身就是文档

### 1.1 变量/函数名说「做什么」，不说「怎么做」

| 反面教材 | 正面教材 |
|---------|---------|
| `let d = new Date()` | `let currentTimestamp = new Date()` |
| `function calc(a, b)` | `function calculateDiscount(originalPrice, memberLevel)` |
| `let flag = true` | `let isPaymentExpired = true` |

**AI 为什么需要**：看到 `d` 不知道这是时间、字符串还是天数；看到 `currentTimestamp` 知道后续该怎么用。`calc` 让 AI 猜不出公式意图，正确的名字能约束 AI 生成合理的运算逻辑。

---

### 1.2 布尔值必须加前缀：`is` / `has` / `can` / `should`

| 反面教材 | 正面教材 |
|---------|---------|
| `visible` | `isModalVisible` |
| `logged` | `hasUserLoggedIn` |
| `admin` | `canAccessAdminPanel` |

**AI 为什么需要**：AI 看到 `is`/`has` 前缀，立刻知道这是布尔值，不会在条件里把它当字符串或数字用。

---

### 1.3 集合用复数，单对象用单数，绝不混用

| 反面教材 | 正面教材 | 灾难场景 |
|---------|---------|---------|
| `let user = []` | `let users = []` | AI 看到 `user` 是数组，可能会写 `user.name` 导致报错 |
| `let itemList = {}` | `let itemMap = {}` 或 `let items = []` | `List` 后缀却是对象，AI 会按数组方法操作 |

**AI 为什么需要**：命名与数据类型的一致性，是 AI 推断 API 用法的第一道防线。

---

### 1.4 类名用名词（单数），方法名用动词，绝不混用

| 反面教材 | 正面教材 | 灾难场景 |
|---------|---------|---------|
| `class ProcessData` | `class OrderProcessor` | AI 把类当方法调用，或把方法当类实例化 |
| `function User()` | `class User` / `function createUser()` | AI 无法判断这是工厂函数还是构造函数 |
| `class Run` | `class TaskRunner` | 名词化动词让 AI 误判为行为而非实体 |

```python
# 正面教材：AI 看到类名知道这是实体，方法名知道这是行为
class PaymentGateway:
    def authorize_transaction(self, amount: Decimal) -> AuthorizationResult: ...
    def refund_payment(self, transaction_id: str) -> RefundResult: ...
```

**AI 为什么需要**：类名与方法名的语法角色必须能从名字直接推断。AI 在跨文件补全、生成调用链时，需要第一时间知道某个标识符是"可实例化的实体"还是"可执行的行为"。

---

## 二、结构规则：让 AI 不迷路

### 2.1 一个函数/类只做一件事（单一职责）

```javascript
// 反面教材：AI 不知道你下一步要改哪部分
function handleLogin() {
  if (input.value === '') return;      // 验证
  const res = fetch('/api/login');      // 请求
  if (res.ok) showSuccess();            // UI
  else showError();
}

// 正面教材：AI 续写时职责清晰，不会乱
function validateLoginInput(input) { ... }
async function requestLogin(credentials) { ... }
function renderLoginResult(state) { ... }
```

```python
# 反面教材：类承载了太多不相关的职责
class UserManager:
    def authenticate(self, password): ...      # 认证
    def send_email(self, message): ...           # 邮件
    def generate_report(self): ...               # 报表
    def backup_database(self): ...               # 运维

# 正面教材：每个类边界清晰，AI 知道该往哪加功能
class Authenticator:
    def authenticate(self, credentials): ...

class EmailService:
    def send(self, recipient, message): ...

class ReportGenerator:
    def generate(self, period): ...
```

**AI 为什么需要**：职责单一的函数和类让 AI 在修改、扩展或重构时，能精确定位影响范围，不会牵一发而动全身。God Class 会让 AI 在后续迭代中不断往同一个文件里塞无关逻辑。

---

### 2.2 拒绝深层嵌套，多用「提前返回」

```javascript
// 反面教材：AI 容易在括号迷宫里迷失，生成语法错误
function process(data) {
  if (data) {
    if (data.items) {
      data.items.forEach(item => {
        if (item.active) {
          // ...
        }
      });
    }
  }
}

// 正面教材：扁平化，AI 每一层都看得清边界
function process(data) {
  if (!data || !data.items) return;

  const activeItems = data.items.filter(item => item.active);
  activeItems.forEach(handleActiveItem);
}
```

**AI 为什么需要**：嵌套深度直接决定 AI 对作用域和变量生命周期的理解难度。扁平化结构让 AI 的上下文推理更可靠。

---

### 2.3 依赖必须显式，禁止「幽灵全局变量」

```javascript
// 反面教材：AI 看不到 window.user 从哪来，也不知道它什么时候变
function showUserName() {
  return window.user.name;  // 幽灵依赖
}

// 正面教材：AI 一眼看到数据从哪来，类型是什么
function showUserName(user) {
  return user.name;
}
```

**AI 为什么需要**：显式参数让 AI 能追踪数据流，幽灵依赖会让 AI 在后续修改中引入不可预测的副作用。

---

### 2.4 优先组合，继承链不超过两层

```python
# 反面教材：AI 要追踪三层继承才能理解行为，且父类变更会连锁破坏
class Animal: ...
class Mammal(Animal): ...
class Primate(Mammal): ...
class Human(Primate): ...

# 正面教材：AI 看到类定义就知道全部行为，没有隐藏继承逻辑
class Human:
    def __init__(self):
        self.locomotion = BipedalLocomotion()   # 组合
        self.cognition = PrimateCognition()       # 组合

# 如果必须继承，保持扁平
class PaymentProcessor(ABC): ...
class StripeProcessor(PaymentProcessor): ...   # 仅一层
class PayPalProcessor(PaymentProcessor): ...     # 仅一层
```

**AI 为什么需要**：继承链越深，AI 越难预测实际运行时行为（方法覆盖、MRO 解析）。组合让依赖关系显式写在构造函数里，AI 不需要回溯继承树就能理解类的能力边界。

---

## 三、类型与契约：给 AI 画边界

### 3.1 数据结构必须显式定义，禁止裸对象/裸字典

```python
# 反面教材：AI 不知道 data 里有什么，只能瞎猜
def display_user(data): ...

# 正面教材：AI 看到 UserProfile 的字段，能自动补全正确的属性
from dataclasses import dataclass

@dataclass
class UserProfile:
    id: str
    display_name: str
    is_verified: bool

def display_user(user: UserProfile) -> str: ...
```

```typescript
// 正面教材（TypeScript 版本）
interface UserProfile {
  id: string;
  displayName: string;
  isVerified: boolean;
}

function displayUser(user: UserProfile): string { ... }
```

**AI 为什么需要**：显式数据结构是 AI 理解系统契约的「脚手架」。裸字典/裸对象等于拆掉了脚手架，让 AI 在黑暗中摸索。

---

### 3.2 接口/抽象类要小而专，禁止「万能接口」

```typescript
// 反面教材：AI 看到 15 个方法，不知道实现时该关注哪些
interface DataHandler {
  create(): void;
  read(): void;
  update(): void;
  delete(): void;
  validate(): boolean;
  serialize(): string;
  deserialize(): string;
  log(): void;
  cache(): void;
  notify(): void;
  // ...
}

// 正面教材：AI 每个接口只关注一个契约，实现时职责清晰
interface Persistable {
  save(): void;
  load(): void;
}

interface Validatable {
  validate(): ValidationResult;
}

interface Loggable {
  log(level: LogLevel, message: string): void;
}

class Order implements Persistable, Validatable { ... }
```

**AI 为什么需要**：接口越小，AI 在生成实现类时越能精准匹配需要覆写的方法。万能接口会让 AI 生成大量空实现或错误实现，因为 AI 无法判断哪些方法是核心、哪些是附属。

---

### 3.3 注释写「为什么」，不写「做什么」

```javascript
// 反面教材：废话，AI 读代码就知道
// 给 count 加 1
count += 1;

// 正面教材：AI 知道业务意图，后续不会误删
// 补偿时区偏移导致跨天时订单统计少算一天
count += 1;
```

**AI 为什么需要**：「做什么」是代码本身能回答的，「为什么」才是 AI 判断后续修改是否安全的关键依据。

---

### 3.4 魔法数字/字符串必须变成有名字的常量

```javascript
// 反面教材：AI 看到 3 不知道是什么，生成代码时不敢动
if (status === 3) { ... }

// 正面教材：AI 看到常量名，理解业务状态机
const ORDER_STATUS_SHIPPED = 3;
if (status === ORDER_STATUS_SHIPPED) { ... }
```

```python
# 反面教材：AI 不知道 "timeout" 在业务中的含义
if error == "timeout": ...

# 正面教材：AI 理解这是网络层错误分类
class ErrorCode:
    NETWORK_TIMEOUT = "timeout"

if error == ErrorCode.NETWORK_TIMEOUT: ...
```

**AI 为什么需要**：命名常量让 AI 把字面量与业务语义绑定，避免在后续修改中误改或误用。

---

## 四、标识符语义化：描述角色，不描述外观

### 4.1 通用原则

任何用于标识实体、资源、模块或接口的名称，都必须描述其**业务角色和内容**，而非其**表现形式或位置**。

| 反面教材（描述外观/位置） | 正面教材（描述角色） |
|------------------------|-------------------|
| `.red-box` | `.error-message` |
| `.big-text` | `.article-title` |
| `.left-column` | `.sidebar-navigation` |
| `table_01` | `user_profiles` |
| `api_v2_endpoint` | `order_payment_gateway` |
| `config.json` | `database_connection_config.json` |

**AI 为什么需要**：标识符是 AI 在跨文件、跨模块推理时的唯一文本线索。描述外观的名字会让 AI 在重构或扩展时误判实体的业务含义。

---

### 4.2 前端专项：CSS 选择器语义化

```html
<!-- 反面教材：AI 读不到业务含义 -->
<div class="p-4 bg-white rounded-lg shadow-md flex flex-col gap-2">

<!-- 正面教材：AI 知道这是订单卡片，后续改样式不会破坏结构 -->
<div class="order-summary-card">
```

**AI 为什么需要**：CSS 类名是 AI 理解 DOM 结构的文本线索。工具类缩写堆叠对 AI 来说是噪声，语义类名是信号。

---

### 4.3 数据库与配置：表名/键名语义化

```sql
-- 反面教材：AI 不知道 t1 存的是什么
CREATE TABLE t1 (id INT, a VARCHAR(255), b BOOLEAN);

-- 正面教材：AI 理解数据模型和关系
CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

```yaml
# 反面教材：AI 不知道这些键控制什么
host: "localhost"
port: 5432

# 正面教材：AI 理解这是数据库连接配置
database_connection:
  host: "localhost"
  port: 5432
  pool_size: 10
```

---

## 五、工程组织：目录即架构

### 5.1 目录名就是架构分层，不要让 AI 猜

```
反面教材：
/src
  /utils        ← 什么都塞，成了垃圾堆
  /helpers
  /misc

正面教材：
/src
  /domain         ← 核心业务逻辑（订单、用户）
  /application    ← 用例/服务层（结账流程）
  /infrastructure ← API 客户端、存储实现
  /presentation   ← 组件、页面、UI 状态
```

**AI 为什么需要**：AI 拿到需求「加一个优惠券功能」，看到 `/domain` 就知道该在哪新建文件，不会乱扔到 `utils.js` 里。

---

## 六、使用方式

### 作为 System Prompt 使用

将以下内容加入你的 AI 工具（如 Kimi、Claude、GPT）的 system prompt 或上下文指令中：

```
你是一位严格遵守「AI 友好代码协议 (AFCP) v1.2.0」的工程师。

所有生成的代码必须遵循以下原则：
1. 命名必须语义化，描述「是什么」而非「长什么样」
2. 布尔值加 is/has/can/should 前缀
3. 集合用复数，单对象用单数
4. 类名用名词（单数），方法名用动词
5. 函数/类单一职责，拒绝深层嵌套，多用提前返回
6. 依赖显式传递，禁止幽灵全局变量
7. 优先组合，继承链不超过两层
8. 数据结构必须显式定义，禁止裸对象/裸字典
9. 接口/抽象类小而专，禁止万能接口
10. 注释写「为什么」不写「做什么」
11. 魔法数字/字符串必须命名常量
12. 标识符语义化：描述角色而非外观（类名、表名、配置键、CSS 类名等）
13. 目录结构反映架构分层

违反以上任何一条，必须重新生成修正后的代码。
```

### 作为代码审查 Checklist

在审查 AI 生成的代码时，逐条对照上述 13 条规则，任何违反都应要求 AI 修正。

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.0.0 | 2026-07-05 | 初始版本，涵盖命名、结构、类型、前端、工程组织五大维度 |
| v1.1.0 | 2026-07-05 | 将「类型即契约」改为跨语言通用的「数据结构显式定义」；将「CSS 选择器语义化」扩展为通用的「标识符语义化」原则；精简 System Prompt 模板至 10 条 |
| v1.2.0 | 2026-07-05 | 融入 OOP 核心规则：类名/方法名命名区分（1.4）、类级别单一职责（2.1）、优先组合限制继承（2.4）、接口隔离（3.2）。System Prompt 模板扩展至 13 条 |

---

> **协议声明**：本协议为开放规范，欢迎根据实际项目需求进行扩展和修订。修订时请遵循语义化版本控制（SemVer），并在版本历史中记录变更。
