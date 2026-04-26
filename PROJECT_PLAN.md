# 智能数据分析系统 — 项目开发计划

## 技术栈

| 层级 | 技术 |
|------|------|
| 大模型 | Qwen3（通义千问，via DashScope API） |
| 后端框架 | FastAPI + LangChain |
| 数据库 | SQLite3（业务数据 business.db + 应用数据 app.db） |
| 前端框架 | React（Vite） |
| 状态管理 | Zustand |
| 图表渲染 | ECharts（echarts-for-react） |
| 流式通信 | SSE（Server-Sent Events） |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (React)                    │
│  ┌──────────────┬──────────────────┬──────────────────┐  │
│  │  会话管理面板  │     问答区域      │   可视化图表面板  │  │
│  │  (Left 20%)  │   (Middle 50%)   │   (Right 30%)   │  │
│  └──────────────┴──────────────────┴──────────────────┘  │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP / SSE
┌───────────────────────────▼─────────────────────────────┐
│                   Backend (FastAPI)                      │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │  Session   │  │  LangChain  │  │   Chart Builder  │  │
│  │  Manager   │  │  SQL Agent  │  │   (结构化输出)    │  │
│  └────────────┘  └──────┬──────┘  └──────────────────┘  │
│                         │                                │
│  ┌──────────────────────▼──────────────────────────────┐ │
│  │           Qwen3 LLM（DashScope API）                 │ │
│  └─────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                      SQLite3                             │
│   business.db（业务数据）  │  app.db（会话/消息历史）     │
└─────────────────────────────────────────────────────────┘
```

### 一次完整查询的数据流

```
用户输入 "统计各部门2024年销售额"
    ↓
POST /chat/stream  { sessionId, message }
    ↓
memory_service 加载该会话历史上下文
    ↓
sql_agent 调用 Qwen3:
  ├── 思考 → 生成 SQL
  ├── 执行 SQL → 获取原始数据
  └── 分析结果 → 输出结构化 JSON
    ↓
SSE 流式推送给前端:
  event: thinking  → 实时显示思考过程
  event: sql       → 展示执行的 SQL
  event: chart     → 图表 JSON 数据
  event: done      → 结束
    ↓
前端 ChartPanel 接收 chart 事件 → ECharts 渲染
```

---

## 目录结构规划

### 后端

```
backend/
├── main.py                    # FastAPI 入口，挂载路由、CORS
├── config.py                  # 环境配置（API Key、DB路径等）
├── .env                       # 环境变量（不提交 git）
├── requirements.txt
│
├── routers/
│   ├── chat.py                # POST /chat/stream（SSE 流式输出）
│   ├── session.py             # CRUD /sessions
│   └── schema.py              # GET /db/schema（返回表结构）
│
├── services/
│   ├── llm_service.py         # Qwen3 LangChain 封装
│   ├── sql_agent.py           # LangChain SQL Agent 核心逻辑
│   ├── memory_service.py      # 会话上下文记忆管理
│   └── chart_service.py       # 解析查询结果 → 图表数据结构
│
├── models/
│   ├── session.py             # Session Pydantic/ORM 模型
│   └── message.py             # Message 模型
│
└── database/
    ├── connection.py          # SQLAlchemy 连接
    ├── session_store.py       # 会话/消息持久化 CRUD
    └── business.db            # 业务数据（示例数据）
```

### 前端

```
frontend/src/
├── App.jsx                    # 路由 + 全局三栏布局
├── main.jsx
│
├── components/
│   ├── SessionPanel/
│   │   ├── SessionPanel.jsx   # 左侧面板容器
│   │   ├── SessionList.jsx    # 历史会话列表
│   │   └── SessionItem.jsx    # 单条会话（重命名/删除）
│   │
│   ├── ChatArea/
│   │   ├── ChatArea.jsx       # 中间面板容器
│   │   ├── MessageList.jsx    # 消息气泡列表
│   │   ├── MessageBubble.jsx  # 单条消息（含 SQL 折叠）
│   │   ├── SqlPreview.jsx     # 可折叠 SQL 语法高亮块
│   │   └── InputBar.jsx       # 输入框 + 发送按钮
│   │
│   └── ChartPanel/
│       ├── ChartPanel.jsx     # 右侧面板容器
│       ├── ChartRenderer.jsx  # 按 chartType 动态渲染 ECharts
│       ├── ChartToolbar.jsx   # 切换图表类型 / 导出 PNG
│       └── EmptyChart.jsx     # 空状态占位
│
├── hooks/
│   ├── useSSE.js              # SSE 流式消费 Hook
│   ├── useSession.js          # 会话操作封装
│   └── useChart.js            # 图表数据状态
│
├── store/
│   └── index.js               # Zustand 全局状态
│
└── services/
    ├── api.js                 # Axios 封装（sessions / schema）
    └── sse.js                 # SSE 连接管理
```

---

## 开发计划（4 Phases）

### Phase 1 — 基础框架搭建与运行验证

> 目标：前后端各自能独立跑起来，Qwen3 能调通

| # | 任务 | 验收标准 |
|---|------|---------|
| 1-1 | 初始化后端目录结构：routers / services / models / database | 目录和 main.py 存在 |
| 1-2 | 安装后端依赖，生成 requirements.txt | pip install 无报错 |
| 1-3 | 配置 config.py，读取 .env 环境变量 | DASHSCOPE_API_KEY 可读取 |
| 1-4 | 启动 FastAPI 基础服务，配置 CORS | http://localhost:8000/docs 可访问 |
| 1-5 | 初始化前端项目（Vite + React），安装依赖 | node_modules 安装完成 |
| 1-6 | 前端基础运行验证 | http://localhost:5173 页面正常渲染 |
| 1-7 | 创建 SQLite3 业务数据库，建表并插入示例数据 | 可用 DB Browser 查看数据 |
| 1-8 | 验证 Qwen3 连通性（单独脚本） | 控制台能打印模型回复 |

---

### Phase 2 — 前端 UI 研发

> 目标：完整三栏 UI 可交互，用 Mock 数据驱动图表和消息

| # | 任务 | 验收标准 |
|---|------|---------|
| 2-1 | 三栏全局布局 App.jsx（左20% / 中50% / 右30%） | 布局固定，无滚动条溢出 |
| 2-2 | 左侧 SessionPanel：列表、新建、激活高亮、重命名、删除 | 交互流畅，状态正确 |
| 2-3 | 中间 ChatArea：消息气泡 + 输入框 + 发送按钮 | 用户/AI 气泡样式区分 |
| 2-4 | SqlPreview 组件：可折叠 + 语法高亮 | 点击折叠/展开正常 |
| 2-5 | 右侧 ChartPanel：ECharts 渲染 bar/line/pie/scatter | Mock 数据四种图表均可渲染 |
| 2-6 | ChartToolbar：切换图表类型 + 导出 PNG | 切换生效，PNG 可下载 |
| 2-7 | Zustand 全局状态（sessionList / currentSessionId / messages / chartData） | 状态跨组件同步 |
| 2-8 | useSSE Hook：解析 thinking/sql/chart/done 四种事件 | Mock SSE 流可驱动 UI 更新 |
| 2-9 | UI 细节：加载动画、流式打字效果、错误 Toast、响应式最小宽度 | 视觉体验完整 |

---

### Phase 3 — 后端接口研发

> 目标：所有接口可通过 /docs 独立测试

| # | 任务 | 验收标准 |
|---|------|---------|
| 3-1 | database/connection.py：SQLAlchemy 连接 business.db（只读）和 app.db（读写） | 连接无报错 |
| 3-2 | database/session_store.py：Session + Message 表 ORM + CRUD | 增删查改正常 |
| 3-3 | services/llm_service.py：封装 ChatTongyi，支持 streaming=True | 流式回复可打印 |
| 3-4 | services/sql_agent.py：SQL Agent + 自定义 System Prompt，输出结构化 chartJSON | 自然语言可转 SQL 并返回图表 JSON |
| 3-5 | services/memory_service.py：按 sessionId 隔离记忆，持久化到 DB | 多会话记忆互不干扰 |
| 3-6 | services/chart_service.py：解析 LLM 输出 JSON → 规范化 ECharts option | 输出格式 ECharts 可直接使用 |
| 3-7 | routers/session.py：GET/POST/PATCH/DELETE /sessions + 历史消息查询 | /docs 测试全部通过 |
| 3-8 | routers/chat.py：POST /chat/stream，SSE 推送 thinking→sql→chart→done | curl 测试 SSE 事件正常 |
| 3-9 | routers/schema.py：GET /db/schema，返回所有表名和字段 | 返回结构正确 |
| 3-10 | SQL 错误自动修正：捕获异常 → 携带错误信息重调 LLM，最多重试 2 次 | 错误 SQL 场景可自动修正 |

---

### Phase 4 — 前后端联调

> 目标：全链路跑通，覆盖正常流程和异常场景

| # | 任务 | 验收标准 |
|---|------|---------|
| 4-1 | 联调会话管理：新建/切换/删除与后端同步，刷新后状态保留 | 数据持久化正确 |
| 4-2 | 联调流式对话：SSE 事件顺序正确，UI 实时渲染思考/SQL/图表 | 全流程无卡顿 |
| 4-3 | 多轮对话验证：追问场景下上下文记忆生效 | 关联查询结果正确 |
| 4-4 | 多图表类型验证：触发 bar/line/pie/scatter 四种图表 | ECharts 渲染均正确 |
| 4-5 | 异常场景测试：SQL 失败自动修正、LLM 超时、空结果集、非数据类问题兜底 | 无白屏、无未捕获异常 |
| 4-6 | 端到端回归：新建会话→多轮问答→图表切换→导出→切换会话→历史记录 | 完整路径无问题 |

---

## API 接口规范（前后端契约）

> 本节描述 **Phase 3 后端实际实现并通过测试** 的接口形态，前端在 Phase 2/4
> 的 mock 与联调代码必须严格按此规范，**字段命名以后端为准（snake_case）**。
>
> 所有路径前缀：`http://localhost:8000`

### 通用约定

| 项 | 取值 |
|---|---|
| 编码 | UTF-8 |
| 错误响应 | `{ "detail": "<错误信息>" }`（FastAPI 默认） |
| 时间字段 | ISO 8601（如 `"2026-04-26T08:55:49.601004"`），UTC，无时区后缀 |
| 字段命名 | **snake_case**（`session_id` / `created_at` / `message_count` / `chart_type` 等） |

### 实体 Schema

#### `Session`

```json
{
  "id":            "s-4378fcef61fd",
  "title":         "各部门销售额对比",
  "created_at":    "2026-04-26T08:55:49.601004",
  "updated_at":    "2026-04-26T08:55:49.711697",
  "message_count": 2
}
```

#### `Message`

```json
{
  "id":         "m-da80e6f7782c",
  "session_id": "s-f3f964dfa272",
  "role":       "user | assistant",
  "content":    "回答正文 ...",
  "thinking":   "可空。assistant 的思考过程",
  "sql":        "可空。仅 assistant 才有",
  "chart":      null,
  "created_at": "2026-04-26T08:49:14.474367"
}
```

#### `Chart`

```json
{
  "chartType": "bar | line | pie | scatter",
  "title":    "图表标题（可选）",
  "xAxis":    ["华东","华北","华南"],
  "series":   [{ "name": "客户数", "data": [3,3,3] }]
}
```

* **bar / line**：`xAxis` 为类目数组，`series[].data` 为数值数组
* **pie**：省略 `xAxis`，`series[0].data` 为 `[{name, value}]`
* **scatter**：`xAxis` 可省略（数值轴），`series[].data` 为 `[[x,y], ...]`

---

### REST 接口

| 方法 | 路径 | 入参 | 出参 |
|---|---|---|---|
| GET | `/sessions` | — | `Session[]`（按 `updated_at` 倒序） |
| POST | `/sessions` | `{title?: string}` | `Session`（201） |
| PATCH | `/sessions/{sid}` | `{title: string}` | `Session` |
| DELETE | `/sessions/{sid}` | — | 204 No Content |
| GET | `/sessions/{sid}/messages` | — | `Message[]`（按 `created_at` 升序） |
| GET | `/db/schema` | — | `TableInfo[]` |
| GET | `/health` | — | `{status: "ok"}` |
| POST | `/chat/stream` | `{session_id, message}` | SSE 流（见下） |

**`TableInfo` 形态**：
```json
{
  "name": "sales",
  "row_count": 800,
  "columns": [
    { "name": "id", "type": "INTEGER", "nullable": true,  "primary_key": true },
    { "name": "order_date", "type": "DATE", "nullable": false, "primary_key": false }
  ]
}
```

---

### SSE 协议（`POST /chat/stream`）

* HTTP `Content-Type: text/event-stream; charset=utf-8`
* 帧分隔符 `\r\n\r\n`（`sse-starlette`）
* 每帧为单行 `event:` + 单行 `data:`（JSON 字符串）
* 每个 SSE 请求对应**一次完整问答**，最后必有 `done` 事件

| 事件 | 出现次数 | data 形态 | 说明 |
|---|---|---|---|
| `thinking` | 1+ | `{ content: string }` | 累计的思考过程文本（每次都包含完整累计内容，不是增量） |
| `sql` | 1~3 | `{ sql: string }` | 完整 SQL；自动重试时会再次发出（最多 3 次：原始 + 2 次修正） |
| `answer` | 1+ | `{ content: string }` | 累计的用户向回答文本（同 thinking，每次完整） |
| `chart` | 0~1 | `{ chartType, title?, xAxis?, series }` | **直接是 chart 对象**，不再嵌套 |
| `error` | 0~1 | `{ message: string }` | 失败时发送 |
| `done` | 1 | `{}` | 流结束，连接关闭 |

**典型事件序列**：

```
event: thinking
data: {"content":"需要 JOIN sales 与 employees..."}

event: sql
data: {"sql":"SELECT d.name, SUM(s.amount) ..."}

event: answer
data: {"content":"销售部"}

event: answer
data: {"content":"销售部 2024 年销售额"}

event: chart
data: {"chartType":"bar","title":"...","xAxis":[...],"series":[...]}

event: done
data: {}
```

**错误自动修正（3-10）**：当生成的 SQL 在 SQLite 上执行失败，后端会发出
一段 `thinking` 解释原因 + 重新发 `sql` 事件（最多 2 次）。前端收到第二个
`sql` 时应**覆盖**而不是追加显示。

---

### 字段映射对照表（前端常见误用）

| ❌ 错误（驼峰） | ✅ 正确（snake_case） | 出现位置 |
|---|---|---|
| `updatedAt` | `updated_at` | Session |
| `messageCount` | `message_count` | Session |
| `createdAt` | `created_at` | Session / Message |
| `sessionId`（请求体） | `session_id` | `POST /chat/stream` |
| `chartData`（直接 chart） | `chart` | Message |
