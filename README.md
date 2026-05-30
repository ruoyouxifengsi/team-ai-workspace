# Team AI Workspace · 团队 AI 工作台

为小型团队（5-20 人）搭建私有 AI 工作台的一套开箱即用方案。每人独立工作区，能上传文件、和 AI 多轮对话、让 AI 读写自己的 docx/xlsx/pdf，沉淀的内容公共资料区共享。

**不是 SaaS，不是聊天机器人**——是部署在自己服务器上、绑自己 API key、文件落在自己硬盘上的工作台。

---

## 这玩意儿能干啥

| 场景 | AI 怎么帮 |
|---|---|
| 写推文 / 方案 | 读历届模板 → 起草 → 自动存 docx → 文件树立刻出现 |
| 整理调研数据 | 读 xlsx → 按规则筛选 / 分组 → 生成新 xlsx |
| 找历史资料 | 全文检索公共资料区，引用相关段落作答 |
| 多任务并行 | 多会话切换，每个话题独立上下文 |

## 不是什么

- **不是流式输出**——回复是阻塞式 HTTP（v1 简单优先）
- **不是图片生成 / PPT 生成 / 上网搜索**——架构留了扩展点，但首版没做
- **不是协同编辑**——每个会话单用户

## 技术栈

- 后端：FastAPI + SQLite + SQLAlchemy 2 + bcrypt
- 前端：React 18 + TypeScript + Vite + Mantine UI 7
- AI：DeepSeek API（OpenAI 兼容；换 OpenAI/Claude/通义只要替换 `app/llm/` 的实现）
- 部署：Docker Compose + Caddy（自动 HTTPS）+ SQLite FTS5 全文检索
- 文件工具：python-docx / openpyxl / pypdf

## 5 分钟快速开始（本地）

```bash
git clone https://github.com/ruoyouxifengsi/team-ai-workspace.git
cd team-ai-workspace
cp .env.example .env
# 改 .env：ADMIN_INITIAL_PASSWORD、DEEPSEEK_API_KEY，生成 FERNET_KEY：
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
docker compose up -d --build
```

浏览器开 http://localhost → 用 `admin` 登录 → 开干。

## 部署到自己的服务器

详见 [`docs/DEPLOY.md`](docs/DEPLOY.md)。Caddy 会自动申请 Let's Encrypt 证书，你只要域名 A 记录指过去。

**重要**：FERNET_KEY 一旦设定就**不能换**（换了所有用户的个人 API key 都解不开）。第一次部署后立刻备份 `.env`。

**中国大陆部署的额外注意**：未备案域名指向大陆云服务器，运营商会 RESET 443 端口的 TLS 握手。解决方案：临时用非标端口（如 8443，见 `Caddyfile` 注释），或备案后回 443，或迁海外节点。

## 架构 30 秒

```
                  ┌─────────────────┐
浏览器  ──HTTPS──▶│   Caddy (443)   │
                  └────┬────────┬───┘
                       │        │
                       ▼        ▼
                  ┌────────┐ ┌────────────────────┐
                  │frontend│ │ backend (FastAPI)  │
                  │(nginx) │ │   ┌──────────┐     │
                  └────────┘ │   │  agent   │     │
                             │   │  loop    │──────▶ DeepSeek API
                             │   └──┬───────┘     │
                             │      │             │
                             │  ┌───▼────┐  ┌────────┐
                             │  │ tools  │  │ chat   │
                             │  │ (9 个) │  │ rooms  │
                             │  └───┬────┘  └────────┘
                             │      │                 │
                             │      ▼                 │
                             │  ┌──────────────────┐  │
                             │  │ SQLite + FS      │  │
                             │  └──────────────────┘  │
                             └─────────────────────────┘
```

设计思路、模块拆分、为什么这么选详见 [`docs/DESIGN.md`](docs/DESIGN.md)。

真实部署案例：[`docs/case-study-xinlu.md`](docs/case-study-xinlu.md)（北京科技大学心路实践团使用反馈）。

## 二次开发

### 改品牌

代码默认带的是「实践团 AI 工作台」字样，作为示例实例。改成你自己团队的：

- `frontend/src/pages/LoginPage.tsx` 标题
- `frontend/src/pages/WorkspacePage.tsx` 头部标题
- `backend/app/agent/prompts.py` 的 SYSTEM_PROMPT 改成你们团队的语气和工作场景

### 加新工具

`backend/app/tools/registry.py` 暴露 `@register_tool` 装饰器。一个文件一个工具，写个函数 + 一个 JSON Schema 描述参数，agent 会自动发现。

```python
from app.tools.registry import register_tool

@register_tool(
    name="my_tool",
    description="工具的简要说明，LLM 会读这段决定要不要调",
    parameters={
        "type": "object",
        "properties": {"x": {"type": "string"}},
        "required": ["x"],
    },
)
def my_tool(x: str, *, db, settings, user_id: int, user_role: str) -> dict:
    return {"result": "..."}
```

### 换 LLM 提供商

`backend/app/llm/` 是个三文件抽象层：

- `base.py` 定义 `LLMClient` Protocol
- `deepseek.py` 是默认实现
- `factory.py` 决定每个用户用哪个 client

接入 OpenAI/Claude/通义/智谱：新建 `openai.py`，实现 `chat()` 方法，改 `factory.py` 的分发逻辑。Protocol 不变 → agent loop 不用动。

## 安全 / 隐私

- 密码 bcrypt 哈希存
- Session token 不可猜 + 数据库可吊销
- 个人 API key Fernet 对称加密存
- 文件路径隔离，admin 才能跨用户访问
- 不发任何 telemetry，不连任何外部统计服务

## 限制

- 单 SQLite + 单进程，**不适合超过 20 人或日均 1000+ 次对话**。要更大请换 PostgreSQL + 多 worker（架构本身支持，配置改改就行）。
- LLM 上下文窗口硬上限 60k token（防止超长会话 timeout），超了让用户新建会话
- 工具调用是阻塞的，最多 20 步，每步重试 2 次
- AI 会胡说，重要内容自己审

## 路线图

- v0.2 流式输出（SSE）— 等团队规模大了体验比较关键
- v0.3 PPT 生成
- v0.4 上网搜索工具
- v1.0 多 LLM 提供商共存 + workspace 级共享会话

## 致谢

M1（基础骨架）和 M2（AI 对话核心）全程在 Claude 协作下完成。如果你对 AI 辅助开发的具体工程实践感兴趣，可以读 [`docs/case-study-xinlu.md`](docs/case-study-xinlu.md) 的"开发过程"一节，记录了 spec → plan → subagent 执行 → review 这套流程在真实小项目里的踩坑与收获。

## License

MIT. 见 [LICENSE](LICENSE)。
