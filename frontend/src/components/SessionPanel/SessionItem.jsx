import { useEffect, useRef, useState } from "react";
import { Pencil, Trash2, Check, X, MessageSquare } from "lucide-react";
import toast from "react-hot-toast";
import clsx from "clsx";

import { useStore } from "../../store/index.js";
import * as api     from "../../services/api.js";
import { formatDateTime } from "../../utils/format.js";

export default function SessionItem({ session }) {
  const isActive             = useStore((s) => s.currentSessionId === session.id);
  const isStreaming          = useStore((s) => s.isStreaming);
  const setCurrent           = useStore((s) => s.setCurrentSession);
  const renameLocal          = useStore((s) => s.renameSession);
  const deleteLocal          = useStore((s) => s.deleteSession);
  const replaceMessages      = useStore((s) => s.replaceMessages);
  const upsertSession        = useStore((s) => s.upsertSession);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft]     = useState(session.title);
  const inputRef              = useRef(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  // 切换到该会话 — 拉取消息 → 替换本地 → 切 currentSessionId
  const handleSelect = async () => {
    if (isActive || editing) return;
    if (isStreaming) {
      toast.error("当前还有进行中的回复");
      return;
    }
    try {
      const msgs = await api.listMessages(session.id);
      replaceMessages(session.id, msgs);
      setCurrent(session.id);
    } catch (e) {
      toast.error("加载会话失败：" + (e.message ?? "未知错误"));
    }
  };

  const startRename = (e) => {
    e.stopPropagation();
    setDraft(session.title);
    setEditing(true);
  };

  const commitRename = async (e) => {
    e?.stopPropagation();
    const t = draft.trim();
    if (!t) {
      toast.error("会话名不能为空");
      return;
    }
    if (t === session.title) {
      setEditing(false);
      return;
    }
    try {
      const updated = await api.renameSession(session.id, t);
      upsertSession(updated);   // 用后端返回的全字段（含 updated_at）
      setEditing(false);
      toast.success("已重命名");
    } catch (e2) {
      toast.error("重命名失败：" + (e2.message ?? "未知错误"));
    }
  };

  const cancelRename = (e) => {
    e?.stopPropagation();
    setEditing(false);
  };

  const handleDelete = async (e) => {
    e.stopPropagation();
    if (!confirm(`删除会话 "${session.title}" ？此操作不可恢复。`)) return;
    try {
      await api.deleteSession(session.id);
      deleteLocal(session.id);
      toast.success("已删除");
    } catch (e2) {
      toast.error("删除失败：" + (e2.message ?? "未知错误"));
    }
  };

  return (
    <li
      className={clsx("si", { "si--active": isActive })}
      onClick={handleSelect}
    >
      <div className="si__icon">
        <MessageSquare size={14} />
      </div>
      <div className="si__main">
        {editing ? (
          <input
            ref={inputRef}
            className="si__input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitRename(e);
              else if (e.key === "Escape") cancelRename(e);
            }}
            onBlur={commitRename}
          />
        ) : (
          <>
            <div className="si__title" title={session.title}>
              {session.title}
            </div>
            <div className="si__meta">
              {formatDateTime(session.updated_at)} · {session.message_count} 条
            </div>
          </>
        )}
      </div>
      <div className="si__actions">
        {editing ? (
          <>
            <button className="si__btn" onClick={commitRename} title="确认">
              <Check size={14} />
            </button>
            <button className="si__btn" onClick={cancelRename} title="取消">
              <X size={14} />
            </button>
          </>
        ) : (
          <>
            <button className="si__btn" onClick={startRename} title="重命名">
              <Pencil size={14} />
            </button>
            <button
              className="si__btn si__btn--danger"
              onClick={handleDelete}
              title="删除"
            >
              <Trash2 size={14} />
            </button>
          </>
        )}
      </div>
    </li>
  );
}
