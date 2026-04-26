import { useState } from "react";
import { Brain, Bot, User, BarChart3 } from "lucide-react";
import clsx from "clsx";

import { useStore } from "../../store/index.js";
import { formatDateTime } from "../../utils/format.js";
import SqlPreview from "./SqlPreview.jsx";

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";
  const setActiveChart = useStore((s) => s.setActiveChart);
  const [thinkingOpen, setThinkingOpen] = useState(false);

  if (isUser) {
    return (
      <div className="mb mb--user">
        <div className="mb__avatar mb__avatar--user">
          <User size={16} />
        </div>
        <div className="mb__bubble mb__bubble--user">
          <div className="mb__content">{message.content}</div>
          <div className="mb__time">{formatDateTime(message.created_at)}</div>
        </div>
      </div>
    );
  }

  // assistant
  return (
    <div className="mb mb--ai">
      <div className="mb__avatar mb__avatar--ai">
        <Bot size={16} />
      </div>
      <div className="mb__bubble mb__bubble--ai">
        {message.thinking && (
          <div
            className={clsx("mb__thinking", { "mb__thinking--open": thinkingOpen })}
            onClick={() => setThinkingOpen((v) => !v)}
          >
            <div className="mb__thinking-head">
              <Brain size={14} />
              <span>思考过程</span>
              <span className="mb__thinking-toggle">
                {thinkingOpen ? "收起 ▴" : "展开 ▾"}
              </span>
            </div>
            {thinkingOpen && (
              <div className="mb__thinking-body">{message.thinking}</div>
            )}
          </div>
        )}

        {message.sql && <SqlPreview sql={message.sql} />}

        <div className="mb__content">
          {message.content || (message.streaming ? <span className="mb__cursor">▎</span> : "")}
          {message.streaming && message.content && <span className="mb__cursor">▎</span>}
        </div>

        {message.chart && (
          <button
            className="mb__chart-link"
            onClick={() => setActiveChart(message.chart)}
            title="在右侧面板查看"
          >
            <BarChart3 size={14} />
            <span>{message.chart.title || "查看图表"}</span>
          </button>
        )}

        <div className="mb__time">{formatDateTime(message.created_at)}</div>
      </div>
    </div>
  );
}
