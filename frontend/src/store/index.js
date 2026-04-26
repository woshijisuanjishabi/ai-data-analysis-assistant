import { create } from "zustand";

const newMsgId = () =>
  "m-" + Math.random().toString(36).slice(2, 8) + Date.now().toString(36).slice(-3);

// ISO 8601（与后端 datetime 序列化一致）
const isoNow = () => new Date().toISOString();

export const useStore = create((set, get) => ({
  // ===== 状态 =====
  sessions: [],
  messagesBySession: {},
  currentSessionId: null,

  // 当前激活的图表（来自最近一条 assistant 消息，或用户在中间气泡里点选）
  activeChart: null,
  // 用户在右侧工具栏选择的图表类型 — null 时跟随 chart.chartType
  chartTypeOverride: null,

  // 流式状态
  isStreaming: false,
  streamingMessageId: null,

  // ===== 派生 =====
  getCurrentMessages: () => {
    const sid = get().currentSessionId;
    return sid ? (get().messagesBySession[sid] ?? []) : [];
  },
  getCurrentSession: () => {
    const sid = get().currentSessionId;
    return get().sessions.find((s) => s.id === sid) ?? null;
  },

  // ===== 会话操作 =====
  setCurrentSession: (id) => {
    const msgs = get().messagesBySession[id] ?? [];
    const lastChart = [...msgs].reverse().find((m) => m.chart)?.chart ?? null;
    set({
      currentSessionId: id,
      activeChart: lastChart,
      chartTypeOverride: null,
    });
  },

  /** 直接以后端返回的 SessionOut 为基础写入。 */
  upsertSession: (session) => {
    set((s) => {
      const idx = s.sessions.findIndex((x) => x.id === session.id);
      const next = idx >= 0
        ? s.sessions.map((x) => (x.id === session.id ? { ...x, ...session } : x))
        : [session, ...s.sessions];
      return { sessions: next };
    });
  },

  /** 用接口返回的整批替换本地。 */
  replaceSessions: (sessions) => set({ sessions }),

  renameSession: (id, title) => {
    set((s) => ({
      sessions: s.sessions.map((x) => (x.id === id ? { ...x, title } : x)),
    }));
  },

  deleteSession: (id) => {
    set((s) => {
      const sessions = s.sessions.filter((x) => x.id !== id);
      const { [id]: _, ...rest } = s.messagesBySession;
      let cur = s.currentSessionId;
      let chart = s.activeChart;
      if (cur === id) {
        cur = sessions[0]?.id ?? null;
        const msgs = cur ? rest[cur] ?? [] : [];
        chart = [...msgs].reverse().find((m) => m.chart)?.chart ?? null;
      }
      return {
        sessions,
        messagesBySession: rest,
        currentSessionId: cur,
        activeChart: chart,
        chartTypeOverride: null,
      };
    });
  },

  /** 用接口返回的整批替换某会话消息。 */
  replaceMessages: (sid, messages) => {
    set((s) => ({
      messagesBySession: { ...s.messagesBySession, [sid]: messages },
    }));
  },

  // ===== 消息操作 =====
  appendUserMessage: (content) => {
    const sid = get().currentSessionId;
    if (!sid) return null;
    const msg = {
      id: newMsgId(),
      session_id: sid,
      role: "user",
      content,
      thinking: null,
      sql: null,
      chart: null,
      created_at: isoNow(),
    };
    set((s) => {
      const list = [...(s.messagesBySession[sid] ?? []), msg];
      const sessions = s.sessions.map((x) =>
        x.id === sid
          ? {
              ...x,
              updated_at: msg.created_at,
              message_count: list.length,
              title: x.message_count === 0 ? content.slice(0, 24) : x.title,
            }
          : x
      );
      return {
        messagesBySession: { ...s.messagesBySession, [sid]: list },
        sessions,
      };
    });
    return msg.id;
  },

  startAssistantMessage: () => {
    const sid = get().currentSessionId;
    if (!sid) return null;
    const id = newMsgId();
    const msg = {
      id,
      session_id: sid,
      role: "assistant",
      content: "",
      thinking: "",
      sql: "",
      chart: null,
      streaming: true,
      created_at: isoNow(),
    };
    set((s) => ({
      messagesBySession: {
        ...s.messagesBySession,
        [sid]: [...(s.messagesBySession[sid] ?? []), msg],
      },
      isStreaming: true,
      streamingMessageId: id,
    }));
    return id;
  },

  patchAssistantMessage: (id, patch) => {
    const sid = get().currentSessionId;
    if (!sid) return;
    set((s) => ({
      messagesBySession: {
        ...s.messagesBySession,
        [sid]: (s.messagesBySession[sid] ?? []).map((m) =>
          m.id === id ? { ...m, ...patch } : m
        ),
      },
      // chart 事件到达时同步右侧面板
      activeChart: patch.chart ?? s.activeChart,
      chartTypeOverride: patch.chart ? null : s.chartTypeOverride,
    }));
  },

  finishAssistantMessage: (id) => {
    const sid = get().currentSessionId;
    if (!sid) return;
    set((s) => ({
      messagesBySession: {
        ...s.messagesBySession,
        [sid]: (s.messagesBySession[sid] ?? []).map((m) =>
          m.id === id ? { ...m, streaming: false } : m
        ),
      },
      isStreaming: false,
      streamingMessageId: null,
    }));
  },

  // ===== 图表操作 =====
  setActiveChart: (chart) => set({ activeChart: chart, chartTypeOverride: null }),
  setChartTypeOverride: (t) => set({ chartTypeOverride: t }),
}));
