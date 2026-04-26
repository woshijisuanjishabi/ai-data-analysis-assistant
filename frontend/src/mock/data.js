/**
 * Mock 数据 — Phase 2/3 用，Phase 4 联调时替换为真实接口。
 *
 * 字段命名严格对齐后端真实返回的 JSON（snake_case）：
 *   Session: { id, title, created_at, updated_at, message_count }
 *   Message: { id, session_id, role, content, thinking?, sql?, chart?, created_at }
 *
 * 详见 PROJECT_PLAN.md - "API 接口规范"。
 */

export const mockSessions = [
  {
    id: "s-1",
    title: "各部门 2024 销售额对比",
    created_at: "2026-04-24T10:00:00",
    updated_at: "2026-04-24T10:32:00",
    message_count: 4,
  },
  {
    id: "s-2",
    title: "电子产品类目趋势分析",
    created_at: "2026-04-23T17:50:00",
    updated_at: "2026-04-23T18:05:00",
    message_count: 2,
  },
  {
    id: "s-3",
    title: "客户区域分布",
    created_at: "2026-04-22T09:00:00",
    updated_at: "2026-04-22T09:14:00",
    message_count: 2,
  },
];

// 每个会话的消息历史 — sessionId -> messages[]
export const mockMessages = {
  "s-1": [
    {
      id: "m-1",
      session_id: "s-1",
      role: "user",
      content: "请统计各部门 2024 年的销售额",
      thinking: null,
      sql: null,
      chart: null,
      created_at: "2026-04-24T10:30:00",
    },
    {
      id: "m-2",
      session_id: "s-1",
      role: "assistant",
      content: "好的，正在为您分析各部门 2024 年的销售情况。从数据看，销售部贡献了 100% 的订单（销售部门负责所有交易）。考虑到您可能想了解的是各部门员工销售业绩，我按员工所在部门做了拆解。",
      thinking: "用户问的是各部门销售额。业务上销售订单都挂在销售部员工名下，所以按部门聚合时只有销售部有数据。我会先用 JOIN 把员工和部门连起来，再按部门 group by。",
      sql: "SELECT d.name AS department, COUNT(s.id) AS orders, ROUND(SUM(s.amount), 2) AS total\nFROM departments d\nJOIN employees e ON e.department_id = d.id\nJOIN sales s ON s.employee_id = e.id\nWHERE strftime('%Y', s.order_date) = '2024'\nGROUP BY d.name\nORDER BY total DESC;",
      chart: {
        chartType: "bar",
        title: "各部门 2024 年销售额",
        xAxis: ["销售部"],
        series: [{ name: "销售额", data: [12450320] }],
      },
      created_at: "2026-04-24T10:32:00",
    },
    {
      id: "m-3",
      session_id: "s-1",
      role: "user",
      content: "再看一下各品类的销售情况",
      thinking: null,
      sql: null,
      chart: null,
      created_at: "2026-04-24T10:35:00",
    },
    {
      id: "m-4",
      session_id: "s-1",
      role: "assistant",
      content: "按品类拆解，电子产品类销售额最高，占总额的 80% 左右；办公家具其次；办公耗材虽然订单数多但单价低，总额最少。",
      thinking: null,
      sql: "SELECT p.category, COUNT(s.id) AS orders, ROUND(SUM(s.amount), 2) AS total\nFROM products p\nJOIN sales s ON s.product_id = p.id\nWHERE strftime('%Y', s.order_date) = '2024'\nGROUP BY p.category\nORDER BY total DESC;",
      chart: {
        chartType: "pie",
        title: "2024 年各品类销售占比",
        series: [{
          name: "销售额",
          data: [
            { name: "电子产品", value: 9876543 },
            { name: "办公家具", value: 2345678 },
            { name: "办公耗材", value: 39842 },
          ],
        }],
      },
      created_at: "2026-04-24T10:36:00",
    },
  ],
  "s-2": [
    {
      id: "m-5",
      session_id: "s-2",
      role: "user",
      content: "查一下 2024 年电子产品每月销售趋势",
      thinking: null,
      sql: null,
      chart: null,
      created_at: "2026-04-23T18:00:00",
    },
    {
      id: "m-6",
      session_id: "s-2",
      role: "assistant",
      content: "2024 全年电子产品销售额呈现波动上升态势，2 月和 5 月是双高峰，年末略有回落。",
      thinking: null,
      sql: "SELECT strftime('%Y-%m', s.order_date) AS month, ROUND(SUM(s.amount), 2) AS total\nFROM sales s JOIN products p ON p.id = s.product_id\nWHERE p.category = '电子产品'\n  AND strftime('%Y', s.order_date) = '2024'\nGROUP BY month\nORDER BY month;",
      chart: {
        chartType: "line",
        title: "2024 电子产品月度销售趋势",
        xAxis: ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"],
        series: [{ name: "销售额", data: [880000,1180000,720000,810000,1230000,640000,990000,950000,720000,1010000,860000,580000] }],
      },
      created_at: "2026-04-23T18:02:00",
    },
  ],
  "s-3": [
    {
      id: "m-7",
      session_id: "s-3",
      role: "user",
      content: "客户分布在哪些区域",
      thinking: null,
      sql: null,
      chart: null,
      created_at: "2026-04-22T09:10:00",
    },
    {
      id: "m-8",
      session_id: "s-3",
      role: "assistant",
      content: "客户主要集中在华东、华南、华北三大区域，西部和华中较少。",
      thinking: null,
      sql: "SELECT region, COUNT(*) AS num FROM customers GROUP BY region ORDER BY num DESC;",
      chart: {
        chartType: "bar",
        title: "客户区域分布",
        xAxis: ["华东", "华北", "华南", "华中", "西北", "西南"],
        series: [{ name: "客户数", data: [3, 3, 3, 1, 1, 1] }],
      },
      created_at: "2026-04-22T09:14:00",
    },
  ],
};

/**
 * Mock SSE 脚本 — 用来在前端没有真实后端时驱动一次问答。
 * 各事件 payload 形态严格对齐后端：
 *   thinking → { content }
 *   sql      → { sql }
 *   answer   → { content }
 *   chart    → { chartType, title?, xAxis?, series }
 *   error    → { message }
 *   done     → {}
 */
export const mockSseScript = {
  thinking: "正在分析您的问题…\n→ 识别意图：销售数据汇总\n→ 准备 SQL 查询",
  sql: "SELECT d.name AS department, ROUND(SUM(s.amount), 2) AS total\nFROM departments d\nJOIN employees e ON e.department_id = d.id\nJOIN sales s ON s.employee_id = e.id\nGROUP BY d.name\nORDER BY total DESC;",
  answer: "根据查询结果，销售部 2024 年全年销售总额约 1245 万元，其中 5 月和 11 月为业绩高峰。建议关注 6 月、12 月的下滑情况。",
  chart: {
    chartType: "bar",
    title: "Mock — 各部门销售额",
    xAxis: ["销售部"],
    series: [{ name: "销售额", data: [12450320] }],
  },
};

// 演示用四种图表，方便切换验证
export const demoCharts = {
  bar: {
    chartType: "bar",
    title: "Demo — 柱状图",
    xAxis: ["华东", "华北", "华南", "西北", "西南", "华中"],
    series: [{ name: "客户数", data: [3, 3, 3, 1, 1, 1] }],
  },
  line: {
    chartType: "line",
    title: "Demo — 折线图",
    xAxis: ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"],
    series: [{ name: "销售额", data: [880,1180,720,810,1230,640,990,950,720,1010,860,580] }],
  },
  pie: {
    chartType: "pie",
    title: "Demo — 饼图",
    series: [{
      name: "销售额",
      data: [
        { name: "电子产品", value: 9876 },
        { name: "办公家具", value: 2345 },
        { name: "办公耗材", value: 398  },
      ],
    }],
  },
  scatter: {
    chartType: "scatter",
    title: "Demo — 散点图",
    series: [{
      name: "客户单价 vs 数量",
      data: [[10,800],[20,1200],[15,950],[8,560],[25,1500],[18,1100],[12,700],[30,1700]],
    }],
  },
};
