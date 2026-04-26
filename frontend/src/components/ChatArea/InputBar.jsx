import { useRef, useState } from "react";
import { Send, Loader2, Square } from "lucide-react";
import toast from "react-hot-toast";

import { useStore } from "../../store/index.js";
import * as api      from "../../services/api.js";

export default function InputBar() {
  const [text, setText] = useState("");
  const isStreaming     = useStore((s) => s.isStreaming);
  const sid             = useStore((s) => s.currentSessionId);

  const append          = useStore((s) => s.appendUserMessage);
  const start           = useStore((s) => s.startAssistantMessage);
  const patch           = useStore((s) => s.patchAssistantMessage);
  const finish          = useStore((s) => s.finishAssistantMessage);
  const replaceMessages = useStore((s) => s.replaceMessages);
  const upsertSession   = useStore((s) => s.upsertSession);

  const ctrlRef = useRef(null);

  const send = async () => {
    const t = text.trim();
    if (!t) return;
    if (isStreaming) {
      toast.error("当前还有进行中的回复");
      return;
    }
    if (!sid) {
      toast.error("请先创建或选择会话");
      return;
    }
    setText("");
    append(t);
    const aid = start();
    if (!aid) return;

    const ctrl = new AbortController();
    ctrlRef.current = ctrl;

    let hadError = false;
    try {
      await api.connectChatStream(
        { session_id: sid, message: t },
        {
          // 后端 envelope → 消息字段
          onThinking: (data) => patch(aid, { thinking: data.content }),
          onSql:      (data) => patch(aid, { sql:      data.sql }),
          onAnswer:   (data) => patch(aid, { content:  data.content }),
          onChart:    (chart) => patch(aid, { chart }),
          onError: (data) => {
            hadError = true;
            toast.error("生成失败：" + (data?.message ?? "未知错误"));
          },
          onDone: () => {},
        },
        ctrl.signal,
      );
    } catch (e) {
      if (e.name === "AbortError") {
        toast("已停止生成", { icon: "⏹" });
      } else if (!hadError) {
        toast.error("连接失败：" + (e.message ?? "未知错误"));
      }
    } finally {
      finish(aid);
      ctrlRef.current = null;
    }

    // 流结束后，与后端对账：拉取真实消息列表（含正确 ID）+ 刷新会话元数据
    if (!hadError) {
      try {
        const [msgs, sessions] = await Promise.all([
          api.listMessages(sid),
          api.listSessions(),
        ]);
        replaceMessages(sid, msgs);
        const updated = sessions.find((s) => s.id === sid);
        if (updated) upsertSession(updated);
      } catch (e) {
        // 对账失败不影响主流程；下次切换会话时会再次拉取
        console.warn("[reconcile] failed:", e);
      }
    }
  };

  const stop = () => {
    if (ctrlRef.current) {
      ctrlRef.current.abort();
    }
  };

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="ib">
      <textarea
        className="ib__input"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={onKey}
        rows={2}
        placeholder={isStreaming ? "正在生成回复…" : "向数据库提问，Enter 发送 / Shift+Enter 换行"}
        disabled={isStreaming}
      />
      {isStreaming ? (
        <button className="ib__send" onClick={stop} title="停止生成">
          <Square size={14} fill="currentColor" />
        </button>
      ) : (
        <button
          className="ib__send"
          onClick={send}
          disabled={!text.trim()}
          title="发送"
        >
          <Send size={16} />
        </button>
      )}
    </div>
  );
}
