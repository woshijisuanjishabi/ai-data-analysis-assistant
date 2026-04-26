import { useEffect, useRef } from "react";

import { useStore } from "../../store/index.js";
import MessageBubble from "./MessageBubble.jsx";

export default function MessageList() {
  const messages = useStore((s) => s.getCurrentMessages());
  const sid      = useStore((s) => s.currentSessionId);
  const scroller = useRef(null);

  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, sid]);

  if (messages.length === 0) {
    return (
      <div className="ml ml--empty" ref={scroller}>
        <div className="ml-empty">
          <div className="ml-empty__icon">💡</div>
          <div className="ml-empty__title">开始你的数据分析</div>
          <div className="ml-empty__hint">
            用自然语言描述你的查询，例如：
            <ul>
              <li>"统计各部门 2024 年销售额"</li>
              <li>"电子产品类目 TOP5 销售产品"</li>
              <li>"2024 年每月销售趋势"</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="ml" ref={scroller}>
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}
    </div>
  );
}
