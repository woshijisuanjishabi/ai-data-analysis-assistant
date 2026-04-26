/**
 * useSSE — 真实后端 /chat/stream 的 React 封装。
 *
 *   const { send, abort, isStreaming } = useSSE();
 *   await send(
 *     { session_id, message },
 *     {
 *       onThinking: (data) => patch({ thinking: data.content }),
 *       onSql:      (data) => patch({ sql:      data.sql     }),
 *       onAnswer:   (data) => patch({ content:  data.content }),
 *       onChart:    (chart) => patch({ chart }),
 *       onError:    (data) => toast.error(data.message),
 *       onDone:     ()     => finish(),
 *     },
 *   );
 *
 * Phase 4 联调时把 InputBar 中的 runMockSse 直接换成 useSSE 即可。
 */

import { useCallback, useRef, useState } from "react";

import { connectChatStream } from "../services/api.js";


export function useSSE() {
  const [isStreaming, setIsStreaming] = useState(false);
  const ctrlRef = useRef(null);

  const abort = useCallback(() => {
    if (ctrlRef.current) {
      ctrlRef.current.abort();
      ctrlRef.current = null;
      setIsStreaming(false);
    }
  }, []);

  const send = useCallback(async (body, handlers) => {
    abort();
    const ctrl = new AbortController();
    ctrlRef.current = ctrl;
    setIsStreaming(true);
    try {
      await connectChatStream(body, handlers, ctrl.signal);
    } finally {
      setIsStreaming(false);
      ctrlRef.current = null;
    }
  }, [abort]);

  return { send, abort, isStreaming };
}
