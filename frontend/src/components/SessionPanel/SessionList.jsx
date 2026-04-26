import { useStore } from "../../store/index.js";
import SessionItem from "./SessionItem.jsx";

export default function SessionList() {
  const sessions = useStore((s) => s.sessions);

  if (sessions.length === 0) {
    return (
      <div className="sp__empty">
        <div className="sp__empty-icon">💬</div>
        <div className="sp__empty-text">还没有会话</div>
        <div className="sp__empty-hint">点击右上角"新建"开始</div>
      </div>
    );
  }

  return (
    <ul className="sp__list">
      {sessions.map((s) => (
        <SessionItem key={s.id} session={s} />
      ))}
    </ul>
  );
}
