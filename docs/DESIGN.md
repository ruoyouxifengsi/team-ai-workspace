# 设计文档

记录这个项目的关键决策、模块边界和取舍。读者画像：想自己 fork 出去搭一套的开发者，希望理解「为什么这么做」而不是只会改代码。

---

## 1. 目标 & 非目标

### 目标

- **5-20 人小团队**用得起、玩得明白的私有 AI 工作台
- 单机部署，不需要 Kubernetes / 不需要专门运维
- 数据完全在自己服务器上，不连外部 SaaS（除 LLM API）
- 每个用户独立工作区 + 一个共享公共资料区
- AI 能读写文件，不只是聊天

### 非目标（首版不做）

- 不做大型 SaaS。20 人以上请换 PostgreSQL + 多 worker
- 不做协同实时编辑
- 不做 SSO / 复杂权限模型
- 不做精细化审计 / 合规级日志
- 不做内置图片生成、PPT 生成、上网搜索（架构留扩展点）

---

## 2. 关键决策

| 决策点 | 选了什么 | 为什么 |
|---|---|---|
| 数据库 | SQLite | 单机够用、零运维、迁移到 PG 也只要改 connection string |
| 后端语言 | Python 3.11 + FastAPI | 生态成熟（docx/xlsx/pdf 库全）、原生 async、类型系统够用 |
| 前端 | React + Mantine | 不喜欢从 0 写 CSS；Mantine 7 默认就好看；TS 兼顾安全感 |
| 输出模式 | 阻塞式 HTTP | 比 SSE 简单 30%，UX 损失可控（90 秒 timeout 内基本能回复完） |
| 会话模型 | 多会话 | 队员经常并行干多件事，单会话上下文会串场 |
| LLM 提供商 | DeepSeek | 国内访问稳定、便宜（百万 token 几元），OpenAI 兼容 |
| Agent 模式 | 全自动 + audit log | 工具调用过程不暴露在 UI（避免被 LLM 的"思考"步骤吓到用户），但全部记录在 messages 表 |
| 配额 | 每人每日 token 上限 + 个人 key 可绕过 | 防 agent 死循环烧钱；提供逃生通道给重度用户 |
| 工具调用 | 函数注册表 + JSON Schema | 加新工具改一个文件 + 重启就行，不用动 agent loop |
| 认证 | 不可猜 token + 数据库可吊销 | 不用 JWT，因为撤销难；session 表里改一行就能踢人 |
| Schema 迁移 | 启动时手写 `upgrade_schema()` | Alembic 对 5-10 人项目太重，手写 30 行 SQL 完事 |
| HTTPS | Caddy 自动 Let's Encrypt | 比 nginx + certbot 省心一个数量级 |
| 全文检索 | SQLite FTS5 | 比 Elasticsearch 轻一万倍，几千个公共文件够用 |
| 加密 | Fernet 对称 | 个人 API key 加密存，密钥放服务器 .env，开发者也不能从数据库直接读 |

---

## 3. 模块拆分

后端：

```
backend/app/
├── auth/        登录、session
├── users/       账号 CRUD（admin 用）
├── files/       文件上传/下载/列表/删除/公共发布
├── tools/       9 个 LLM 可调用工具（list/read/write text+docx+xlsx, read_pdf, search_public）
├── agent/       run_loop 主循环、SYSTEM_PROMPT
├── chat/        会话 + 消息 CRUD、build_context 把数据库还原成 OpenAI 格式
├── llm/         LLM Protocol + DeepSeek 实现 + factory
├── quota/       每日 token 配额 + 重置
├── feedback/    用户反馈通道
├── me/          /api/me/settings（看自己用量、绑个人 key）
├── crypto/      Fernet 加解密
└── migrate.py   启动时跑一次的 schema 升级
```

每个目录是一个独立模块，内聚高、耦合低。新人 / AI 上手时基本一个目录看完就能干活。

前端：

```
frontend/src/
├── api/         按后端模块分一一对应的 ts 客户端
├── pages/       路由 = 页面（Login / Workspace / Settings / AdminUsers / AdminFeedback）
├── components/  可复用 UI（FileTree、ChatPane、MessageBubble、ConversationList、MessageInput）
└── store/       Zustand 全局 auth state
```

三栏布局：**左**文件树（个人 + 公共）/ **中**对话 / **右**会话列表。

---

## 4. 数据流：一次对话发生了什么

```
用户输入「读 plan.docx 然后改成更口语化的版本，存为 plan_v2.docx」
                ↓
POST /api/chat/conversations/{id}/send
                ↓
chat/routes.py: 长度 ≤ 10000 字 → 调 run_loop()
                ↓
agent/loop.py:
  1. make_client_for_user(user)  → 用 team key 或 personal key
  2. check_and_reset_quota(user) → 跨日重置 daily_token_used
  3. quota 没满 → 继续；满了 → raise QuotaExceeded → 429
  4. 把 user message 持久化到 messages 表
  5. build_context() 把整个会话历史还原成 OpenAI 格式 list
  6. 估算 token 数，> 60k 则 raise ContextTooLong → 413
  7. 循环 ≤ 20 步：
      llm.chat(messages, tools_schema)
        → 收到 {tool_calls: [{"name": "read_docx", "args": {"file_id": 17}}]}
        → 持久化 assistant 消息（带 tool_calls）
        → execute("read_docx", {"file_id": 17}, user_id=...)  # 权限在这里检查
        → 持久化 tool 结果
        → 继续下一轮
      ...
      llm.chat(...)
        → 收到 {content: "已为你生成 [plan_v2.docx](download:42)", tool_calls: []}
        → 持久化最终 assistant 消息
        → return content
  8. finally: 扣 token 配额（即使失败也扣，防死循环作弊）+ close llm client
                ↓
返回 {assistant_content: "已为你生成 [plan_v2.docx](download:42)"}
                ↓
前端 react-markdown 渲染 → 拦截 download: 协议 → 转成可点击按钮
                ↓
点按钮 → triggerDownload(42, "plan_v2.docx") → blob 下载
```

---

## 5. 工具系统：为什么这样设计

每个工具是一个 Python 函数，挂 `@register_tool` 装饰器。装饰器把它注册到全局 `_TOOLS` 字典，agent 启动时 `all_schemas()` 把所有注册的 schema 拼成 LLM 的 tools 数组。

```python
@register_tool(
    name="read_docx",
    description="Read a .docx Word document and return its paragraph text.",
    parameters={
        "type": "object",
        "properties": {"file_id": {"type": "integer"}},
        "required": ["file_id"],
    },
)
def read_docx(file_id: int, *, db, settings, user_id: int, user_role: str) -> dict:
    row = require_visible(db, file_id, user_id, user_role)  # 权限在这里
    ...
```

关键约束：

- **AI 永远拿不到 user_id**，由 agent 通过 `**ctx` 注入。LLM 想偷读别人的文件也偷不到。
- **所有 read 都走 `get_file_if_visible(file_id, user_id, user_role)`**，权限规则统一一处。
- **所有 write 强制 `owner_id=user_id`**，没法写别人的工作区。
- **读返回 > 50KB 自动截断**附 `[...truncated]`，保护 LLM 上下文。
- **工具调用抛异常自动捕获**，返回 `{"error": "..."}` 给 LLM 自己重试，不杀会话。

加新工具的清单：

1. 在 `tools/` 下新建一个文件
2. 写函数 + `@register_tool` 装饰器
3. agent loop 的 `_import_all_tools()` 里加一行 import
4. 加单元测试（看任何已有 tool 测试照抄结构）

工程上就这么简单，不用动 agent loop 一行代码。

---

## 6. 配额：为什么这么折腾

5-10 人团队公用一个 DeepSeek key 时，最大风险不是「人均用太多」，是「某个 agent 死循环烧光余额」。所以：

- 每人每天 100 万 token 上限（远超日常单人用量；除非 agent 失控）
- 跨日**懒重置**：每次 send 时检查 `daily_token_reset_at < 今天 4 点北京时间` → 重置；不用定时任务
- 扣费在**run_loop 的 finally 里**，无论成功失败都扣，防止「故意触发 MAX_STEPS 异常来不扣钱」
- 用户可以在设置里**绑自己的 DeepSeek key**。绑了之后所有调用走个人余额，bypass 公共池配额——重度用户能逃生

加密：

- 个人 key 不能明文存数据库（数据库泄露 = key 泄露）
- Fernet 对称加密，密钥放服务器 `.env` 的 `FERNET_KEY`
- 一旦设定**不能换**：换了所有用户的个人 key 都解不开
- 部署后立刻把 `.env` 备份到密码管理器

---

## 7. 部署架构

```
                          DNS A 记录
                              ↓
                         你的服务器 IP
                              ↓
                    ┌──────────────────┐
                    │   Caddy (443)    │
                    │  Let's Encrypt   │
                    │  reverse proxy   │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         路径 /api/*    其他路径
              │              │
              ▼              ▼
      ┌────────────┐  ┌──────────────┐
      │  backend   │  │   frontend   │
      │  :8000     │  │  nginx :80   │
      │  (FastAPI) │  │  (静态)      │
      └─────┬──────┘  └──────────────┘
            │
            ▼
      ┌──────────────────────┐
      │   sqlite + 文件      │
      │   ./data 目录        │
      │   (docker volume)    │
      └──────┬───────────────┘
             │
             ▼
      ┌──────────────────────┐
      │   backup 容器        │
      │  每日 cron sqlite    │
      │  + tarball 归档      │
      └──────────────────────┘
```

4 个容器：caddy、backend、frontend、backup。`docker compose up -d --build` 一条命令起。

数据持久化：所有数据落在宿主机 `./data/`，docker volume 挂载。备份容器每天定时 `sqlite3 .backup` + 打 tar 包，扔到 `./data/backups/`。要更可靠的话扔个脚本同步到对象存储。

---

## 8. 扩展点

架构里留了哪些口子：

- **换 LLM 提供商**：`llm/base.py` 是 Protocol，新增 `llm/openai.py` / `llm/claude.py` / `llm/qwen.py` 实现 `chat()`，改 `factory.py` 分发逻辑，agent loop 不动
- **加新工具**：见第 5 节
- **加新 REST 路由**：仿照 `chat/routes.py` 建个新模块，`main.py` 里 include_router
- **加流式输出**：把 `chat/routes.py:send()` 改成 EventSourceResponse，agent loop 配套改成生成器；前端用 EventSource API
- **加图片 / PPT 生成**：作为新工具加，调外部 API（图片：通义/SD；PPT：python-pptx）
- **加上网搜索工具**：调 Bing / Tavily / Serper API
- **加多用户协作**：要在 conversations 表加 `owner_id` 之外的 `participant_ids`，REST 层加共享逻辑

---

## 9. 测试策略

- 后端：121 个 pytest，覆盖 service / route / agent / tools / quota / chat
- 前端：17 个 vitest，覆盖关键组件（MessageInput / MessageBubble / ConversationList / 各 hook）
- E2E：手工冒烟清单（README 里）
- 不做的：性能压测、真烧 token 的 LLM 集成测试

---

## 10. 我们踩过的坑

记录一下首次部署时遇到的实际问题，免得后来者重蹈：

| 坑 | 解决 |
|---|---|
| Caddy 部分容器重启后 DNS misbehaving | 整体 `docker compose down && up -d` |
| pydantic-settings 把 CSV 当成 JSON 报错 | 自定义 `CommaSeparatedListEnvSource` |
| 中国大陆运营商 DPI RESET 443 端口 TLS | 换 8443 高位端口，或备案 |
| pip install timeout（cryptography / pypdf 等大包） | Dockerfile 改清华镜像 `-i https://pypi.tuna.tsinghua.edu.cn/simple` |
| react-markdown v9 strip 掉 `download:` URL | 加 `urlTransform` prop 白名单 |
| Mantine ScrollArea 在 jsdom 没 ResizeObserver | tests/setup.ts 加 mock |
| `_session_factory` 在 test 模块加载时还是 None | 测试里推迟到函数内 import |
| `User.__init__` override 干扰 SQLAlchemy | 改成测试时 commit + refresh 验证默认值 |
| docker-compose.yml 没把新 .env 变量传给容器 | 手动列每个变量名（这是 docker compose 的硬要求） |

---

## 11. 后端代码约定

- `noqa: B008` for `Depends(...)` defaults（FastAPI 必须这么写，但 flake8 不喜欢）
- 函数级 import 只在「会引入循环依赖」或「按需加载重模块」时用
- 数据库 commit 在 service 层而不是 route 层（事务粒度方便控制）
- Pydantic schema 全部在 `schemas.py`，service 不依赖 schema（只返回 ORM 对象）
- 测试用真 SQLite + 真 FS（tmp_path），不用 mock 数据库（mocked DB 测出来 prod 还会爆）

---

## 12. 演化（v0.1 → v0.2 → ...）

打算这么走：

1. **v0.1（当前）**：5-10 人能跑起来、AI 对话 + 9 个文件工具
2. **v0.2**：流式输出（用户等待感受改善）+ 工具调用过程可选地暴露在 UI（debug 用）
3. **v0.3**：图片 / PPT 生成工具
4. **v0.4**：上网搜索工具
5. **v1.0**：多 LLM 提供商共存（同一个 workspace 不同用户用不同 model）+ workspace 级共享会话

每一步都希望保持「单机 docker compose 起得来」的特性，不引入额外 infra 依赖。

---

如果你打算 fork 出去做更大的事，建议先读 `case-study-xinlu.md`，看看真实使用反馈再决定取舍。
