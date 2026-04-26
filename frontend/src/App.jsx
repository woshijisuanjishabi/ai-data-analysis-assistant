import { useEffect, useState } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";

import { useStore }     from "./store/index.js";
import * as api         from "./services/api.js";
import SessionPanel from "./components/SessionPanel/SessionPanel.jsx";
import ChatArea     from "./components/ChatArea/ChatArea.jsx";
import ChartPanel   from "./components/ChartPanel/ChartPanel.jsx";

import "./App.css";

export default function App() {
  const replaceSessions = useStore((s) => s.replaceSessions);
  const replaceMessages = useStore((s) => s.replaceMessages);
  const setCurrent      = useStore((s) => s.setCurrentSession);

  const [bootState, setBootState] = useState("loading"); // loading | ready | failed
  const [bootError, setBootError] = useState(null);

  // 启动时拉取会话列表
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const sessions = await api.listSessions();
        if (cancelled) return;
        replaceSessions(sessions);

        if (sessions.length > 0) {
          const first = sessions[0];
          const msgs  = await api.listMessages(first.id);
          if (cancelled) return;
          replaceMessages(first.id, msgs);
          setCurrent(first.id);
        }
        setBootState("ready");
      } catch (e) {
        if (cancelled) return;
        console.error("[boot] failed:", e);
        setBootError(e.message ?? String(e));
        setBootState("failed");
      }
    })();
    return () => { cancelled = true; };
  }, [replaceSessions, replaceMessages, setCurrent]);

  if (bootState === "loading") {
    return <BootShell><Loader2 className="boot__spin" size={32} /><div>正在连接后端…</div></BootShell>;
  }
  if (bootState === "failed") {
    return (
      <BootShell>
        <AlertCircle size={32} color="#ef4444" />
        <div>无法连接后端</div>
        <div className="boot__hint">{bootError}</div>
        <div className="boot__hint">请确认 backend 运行于 http://localhost:8000</div>
        <button className="boot__retry" onClick={() => window.location.reload()}>重试</button>
      </BootShell>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__title">智能数据分析系统</div>
        <div className="app-header__sub">基于 Qwen3 + LangChain SQL Agent</div>
      </header>
      <div className="app-body">
        <aside className="app-pane app-pane--left">
          <SessionPanel />
        </aside>
        <main className="app-pane app-pane--center">
          <ChatArea />
        </main>
        <aside className="app-pane app-pane--right">
          <ChartPanel />
        </aside>
      </div>
    </div>
  );
}

function BootShell({ children }) {
  return (
    <div className="boot">
      <div className="boot__inner">{children}</div>
    </div>
  );
}
