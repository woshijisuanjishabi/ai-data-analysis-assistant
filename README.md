# 智能数据分析系统

一个基于自然语言的数据分析助手。用户可以直接用中文提问，例如"统计 2024 年各品类销售额"或"客户主要分布在哪些区域"，系统会自动理解问题、生成 SQL、查询业务数据库，并以文字答案和图表形式返回分析结果。

本项目用于探索 AI 在企业数据分析场景中的产品化落地：降低非技术用户使用数据的门槛，让业务人员不依赖 SQL 或 BI 配置，也能完成常见经营分析。

本项目由本人独立完成产品设计和全栈开发，从需求定义、系统架构到接口契约均有完整规划。

---

## 项目定位

传统数据分析流程通常需要业务人员提出需求，数据分析师编写 SQL，再通过 BI 工具制作图表。这个流程响应慢、沟通成本高，也限制了业务人员的自助分析能力。

本项目希望验证一种更自然的交互方式：

> 用户用自然语言提出业务问题，AI 自动完成数据理解、SQL 查询、结果解释和图表生成。

**目标用户**

- 销售负责人
- 运营人员
- 业务分析师
- 管理层助理
- 需要快速查看经营数据但不会写 SQL 的业务人员

---

## 产品设计取舍

**为什么展示 SQL？**
对于企业数据分析场景，用户不仅需要答案，也需要知道答案是怎么来的。展示 SQL 可以提升可信度，也方便技术人员审核。

**为什么使用 SSE？**
数据分析类 AI 应用通常存在等待时间。SSE 可以让用户实时看到模型思考、SQL 生成和回答过程，降低"系统卡住了"的感受。

**为什么先使用 SQLite？**
项目早期目标是验证产品流程，而不是搭建复杂数据仓库。SQLite 足够模拟结构化业务数据，也便于本地运行和面试演示。

**为什么没有直接接入 MCP？**
当前版本优先验证自然语言分析闭环，因此后端直接封装数据库访问。后续如果扩展到多数据源、企业工具或文件系统，可以将数据库、文档库、BI 工具封装为 MCP tools，再由 Agent 调用。

---

## 核心能力

- **自然语言提问**：用户可以直接输入中文业务问题，无需了解数据库结构
- **自动生成 SQL**：系统基于数据库 schema 和用户问题生成可执行 SQL
- **查询真实业务数据**：后端连接 SQLite 示例业务数据库，模拟企业销售分析场景
- **流式回答**：使用 SSE 实时返回思考过程、SQL、回答和图表数据，减少等待感
- **图表生成**：支持柱状图、折线图、饼图、散点图等常见分析图表
- **SQL 可解释**：前端展示 AI 生成的 SQL，方便用户理解分析依据，也便于排查错误
- **多轮会话**：系统保存会话和消息历史，为后续追问和上下文分析提供基础

---

## 示例问题

```text
统计 2024 年各部门销售额
各品类销售额占比是多少？
2024 年每月销售趋势
客户主要分布在哪些区域？
电子产品类目 TOP5 销售产品
```

---

## 产品流程

一次完整的数据分析流程如下：

```
用户输入自然语言问题
        ↓
前端发送请求到 /chat/stream
        ↓
后端加载当前会话历史
        ↓
LangChain 调用 Qwen 模型理解问题
        ↓
生成 SELECT SQL
        ↓
查询 business.db
        ↓
模型总结查询结果
        ↓
生成回答文本和图表 JSON
        ↓
通过 SSE 流式返回前端
        ↓
前端展示回答、SQL 和 ECharts 图表
```

---

## 技术架构

**Frontend**
- React + Vite
- Zustand（状态管理）
- ECharts（图表渲染）
- Server-Sent Events（流式通信）

**Backend**
- FastAPI
- LangChain + Qwen / DashScope
- SQLAlchemy
- SQLite

---

## 系统结构

```
数据分析/
├── PROJECT_PLAN.md
├── README.md
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── routers/
│   │   ├── chat.py
│   │   ├── session.py
│   │   └── schema.py
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── sql_agent.py
│   │   ├── memory_service.py
│   │   └── chart_service.py
│   ├── models/
│   ├── database/
│   │   ├── connection.py
│   │   ├── seed_business.py
│   │   └── session_store.py
│   └── scripts/
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── components/
        ├── services/
        ├── store/
        ├── hooks/
        └── mock/
```

---

## 数据库设计

项目使用两个 SQLite 数据库：

**business.db** — 模拟企业销售业务数据，包括：
- `departments`：部门
- `employees`：员工
- `products`：产品
- `customers`：客户
- `sales`：销售订单

**app.db** — 保存应用数据，包括：
- `sessions`：会话
- `messages`：消息历史

这种拆分让业务数据保持只读，应用数据单独写入，降低 AI 生成 SQL 对业务库造成破坏的风险。

---

## 安全设计

为了降低大模型生成 SQL 带来的风险，当前版本做了以下限制：

- 只允许生成和执行 `SELECT`
- 禁止 `INSERT`、`UPDATE`、`DELETE`、`DROP`、`ALTER` 等写操作
- `business.db` 连接层开启只读保护（`PRAGMA query_only = ON`）
- SQL 执行失败时不会直接中断，而是尝试带错误信息重新生成 SQL（最多重试 2 次）
- 前端展示 SQL，保证分析过程可追溯

---

## 前后端接口

后端以真实接口字段为准，前端在联调阶段严格对齐后端返回。

**会话接口**

```
GET    /sessions
POST   /sessions
PATCH  /sessions/{sid}
DELETE /sessions/{sid}
GET    /sessions/{sid}/messages
```

Session 返回结构：

```json
{
  "id": "s-4378fcef61fd",
  "title": "各部门销售额对比",
  "created_at": "2026-04-26T08:55:49.601004",
  "updated_at": "2026-04-26T08:55:49.711697",
  "message_count": 2
}
```

消息结构：

```json
{
  "id": "m-da80e6f7782c",
  "session_id": "s-f3f964dfa272",
  "role": "assistant",
  "content": "回答正文",
  "thinking": "思考过程",
  "sql": "SELECT ...",
  "chart": null,
  "created_at": "2026-04-26T08:49:14.474367"
}
```

**流式问答接口**

`POST /chat/stream`

请求体：

```json
{
  "session_id": "s-xxx",
  "message": "统计 2024 年各品类销售额"
}
```

SSE 事件：

```
thinking → { content }
sql      → { sql }
answer   → { content }
chart    → { chartType, title, xAxis, series }
error    → { message }
done     → {}
```

---

## 本地运行

**后端**

```bash
cd backend
venv/Scripts/python -m pip install -r requirements.txt
```

创建 `.env`（参考 `.env.example`）：

```env
DASHSCOPE_API_KEY=your_api_key_here
QWEN_MODEL=qwen-plus
```

初始化示例业务数据库：

```bash
venv/Scripts/python database/seed_business.py
```

启动服务：

```bash
venv/Scripts/python main.py
```

接口文档：http://localhost:8000/docs

**前端**

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:5173

---

## 当前进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 | 基础框架：FastAPI 后端、React 前端、SQLite 示例库、Qwen 配置 | 已完成 |
| Phase 2 | 前端 UI：三栏工作台、会话列表、聊天区域、SQL 展示、图表面板、Mock 流式交互 | 已完成 |
| Phase 3 | 后端接口：会话 CRUD、LangChain + Qwen 调用、自然语言转 SQL、SSE 流式输出 | 已完成 |
| Phase 4 | 前后端联调：字段对齐、真实 SSE、多轮对话验证、异常场景验证 | 已完成 |

---

## 后续规划

- 支持上传 CSV / Excel，分析自定义数据
- 支持多数据源连接
- 增强 SQL 生成稳定性
- 增加图表类型推荐逻辑
- 增加用户可编辑图表配置
- 增加权限控制和数据脱敏
- 引入 MCP，将数据库、文档、BI 系统抽象为可调用工具
- 增加分析报告导出能力

---

## 项目亮点

- 从产品需求、系统架构到接口契约都有完整规划
- 不是单纯聊天机器人，而是面向明确业务场景的数据分析工具
- 具备 AI 产品经理需要关注的关键问题：用户场景、交互流程、可信度、异常处理、数据安全和可扩展性
- 使用真实前后端架构和 LLM 调用链路，适合面试中展示产品落地能力
