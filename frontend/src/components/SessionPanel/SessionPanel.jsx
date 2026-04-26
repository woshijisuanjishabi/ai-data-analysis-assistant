import { useState } from "react";
import { Plus, Loader2 } from "lucide-react";
import toast from "react-hot-toast";

import { useStore } from "../../store/index.js";
import * as api      from "../../services/api.js";
import SessionList from "./SessionList.jsx";

import "./SessionPanel.css";

export default function SessionPanel() {
  const upsertSession   = useStore((s) => s.upsertSession);
  const replaceMessages = useStore((s) => s.replaceMessages);
  const setCurrent      = useStore((s) => s.setCurrentSession);

  const [busy, setBusy] = useState(false);

  const handleNew = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const sess = await api.createSession({ title: "新会话" });
      upsertSession(sess);
      replaceMessages(sess.id, []);
      setCurrent(sess.id);
    } catch (e) {
      toast.error("新建失败：" + (e.message ?? "未知错误"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="sp">
      <div className="sp__header">
        <span className="sp__header-title">会话</span>
        <button
          className="sp__new-btn"
          onClick={handleNew}
          disabled={busy}
          title="新建会话"
        >
          {busy ? <Loader2 size={16} className="ib__spin" /> : <Plus size={16} />}
          <span>新建</span>
        </button>
      </div>
      <div className="sp__body">
        <SessionList />
      </div>
    </div>
  );
}
