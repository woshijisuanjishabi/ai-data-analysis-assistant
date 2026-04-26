/**
 * Mock SSE 流 — 严格模拟后端 /chat/stream 的事件包络。
 * Phase 4 联调时 InputBar 会切到 services/api.js 的 connectChatStream，
 * 业务回调签名保持不变。
 *
 * 后端事件 (详见 PROJECT_PLAN.md 接口规范)：
 *   thinking → { content }
 *   sql      → { sql }
 *   answer   → { content }
 *   chart    → { chartType, title?, xAxis?, series }
 *   error    → { message }
 *   done     → {}
 */

import { mockSseScript, demoCharts } from "../mock/data.js";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function pickChart(question) {
  const q = question.toLowerCase();
  if (q.includes("趋势") || q.includes("月") || q.includes("时间")) return demoCharts.line;
  if (q.includes("占比") || q.includes("分布") || q.includes("结构")) return demoCharts.pie;
  if (q.includes("散点") || q.includes("关系") || q.includes("相关")) return demoCharts.scatter;
  return mockSseScript.chart;
}

/**
 * @param {string}  question  用户输入
 * @param {object}  cbs       handlers，与真实 SSE 同样的回调签名
 *   - onThinking(data) — data = { content }
 *   - onSql(data)      — data = { sql }
 *   - onAnswer(data)   — data = { content }
 *   - onChart(data)    — data = chart (chartType/title/xAxis/series)
 *   - onError(data)    — data = { message }
 *   - onDone(data)     — data = {}
 * @returns Promise<void>
 */
export async function runMockSse(question, cbs = {}) {
  const {
    onThinking, onSql, onAnswer, onChart, onError, onDone,
  } = cbs;
  try {
    // ① thinking — 逐段累计推送
    const thinking = mockSseScript.thinking;
    let acc = "";
    for (const piece of thinking.split(/(?<=\n)/)) {
      await sleep(220);
      acc += piece;
      onThinking?.({ content: acc });
    }

    // ② sql — 一次推送（与后端格式一致：{ sql }）
    await sleep(300);
    onSql?.({ sql: mockSseScript.sql });

    // ③ chart — 紧随其后推送图表 JSON（直接传 chart 对象，与后端一致）
    await sleep(400);
    onChart?.(pickChart(question));

    // ④ answer — 流式打字（按字符 chunk）
    const answer = mockSseScript.answer;
    let typed = "";
    for (let i = 0; i < answer.length; i++) {
      typed += answer[i];
      const ch = answer[i];
      const delay = "，。、；：".includes(ch) ? 50 : 20;
      onAnswer?.({ content: typed });
      await sleep(delay);
    }

    // ⑤ done
    onDone?.({});
  } catch (e) {
    onError?.({ message: e.message ?? String(e) });
    throw e;
  }
}
