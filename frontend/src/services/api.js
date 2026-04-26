/**
 * 后端 REST 客户端 + 真实 SSE 流。
 *
 * 接口规范以 backend/main.py 实现为准（详见 PROJECT_PLAN.md "API 接口规范"）。
 * 字段全部 snake_case：session_id / created_at / updated_at / message_count
 *
 * 用法：
 *   import * as api from "../services/api.js";
 *   const sessions = await api.listSessions();
 *   const id = await api.createSession({ title: "新会话" });
 *
 *   await api.connectChatStream(
 *     { session_id, message },
 *     { onThinking, onSql, onAnswer, onChart, onError, onDone },
 *     abortSignal,
 *   );
 */

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function http(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      detail = j.detail ?? detail;
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}


// ====================================================
// /sessions
// ====================================================
export const listSessions   = ()                  => http("/sessions");
export const createSession  = (body = {})         => http("/sessions",         { method: "POST",   body: JSON.stringify(body) });
export const renameSession  = (sid, title)        => http(`/sessions/${sid}`,  { method: "PATCH",  body: JSON.stringify({ title }) });
export const deleteSession  = (sid)               => http(`/sessions/${sid}`,  { method: "DELETE" });
export const listMessages   = (sid)               => http(`/sessions/${sid}/messages`);


// ====================================================
// /db/schema
// ====================================================
export const getDbSchema    = () => http("/db/schema");


// ====================================================
// /chat/stream — 真实 SSE 流
// ====================================================
function parseSseFrame(frame) {
  let event = "message";
  const dataLines = [];
  for (const line of frame.split(/\r?\n/)) {
    if (line.startsWith(":")) continue;       // 注释/心跳
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
  }
  const dataStr = dataLines.join("\n");
  let data = dataStr;
  try { data = JSON.parse(dataStr); } catch { /* keep raw */ }
  return { event, data };
}

/**
 * 与后端 SSE 协议完全对应。回调签名与 mock 一致，便于切换。
 *
 * @param {{session_id: string, message: string}} body
 * @param {{
 *   onThinking?, onSql?, onAnswer?, onChart?, onError?, onDone?
 * }} handlers
 * @param {AbortSignal} [signal]
 */
export async function connectChatStream(body, handlers = {}, signal) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`SSE 请求失败：${res.status} ${res.statusText}`);
  }

  const reader  = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buf = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    // SSE 帧分隔符兼容 \r\n\r\n / \n\n
    buf = buf.replace(/\r\n/g, "\n");
    let idx;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const frame = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      if (!frame.trim()) continue;
      const { event, data } = parseSseFrame(frame);
      const fn = {
        thinking: handlers.onThinking,
        sql:      handlers.onSql,
        answer:   handlers.onAnswer,
        chart:    handlers.onChart,
        error:    handlers.onError,
        done:     handlers.onDone,
      }[event];
      fn?.(data);
    }
  }
}
