import { useStore } from "../../store/index.js";
import MessageList from "./MessageList.jsx";
import InputBar    from "./InputBar.jsx";

import "./ChatArea.css";

export default function ChatArea() {
  const session = useStore((s) => s.getCurrentSession());

  if (!session) {
    return (
      <div className="ca ca--empty">
        <div className="ca-empty">
          <div className="ca-empty__icon">📊</div>
          <div className="ca-empty__title">还没有会话</div>
          <div className="ca-empty__hint">请先在左侧创建一个会话</div>
        </div>
      </div>
    );
  }

  return (
    <div className="ca">
      <div className="ca__header">
        <span className="ca__title" title={session.title}>{session.title}</span>
        <span className="ca__sub">{session.message_count} 条消息</span>
      </div>
      <div className="ca__body">
        <MessageList />
      </div>
      <div className="ca__footer">
        <InputBar />
      </div>
    </div>
  );
}
