import { useState } from "react";
import { Highlight, themes } from "prism-react-renderer";
import { Copy, Check, Database } from "lucide-react";
import toast from "react-hot-toast";

export default function SqlPreview({ sql }) {
  const [open, setOpen]     = useState(true);
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      toast.success("SQL 已复制");
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("复制失败");
    }
  };

  return (
    <div className="sql">
      <div className="sql__head" onClick={() => setOpen((v) => !v)}>
        <Database size={14} />
        <span className="sql__title">SQL</span>
        <button
          className="sql__copy"
          onClick={handleCopy}
          title="复制"
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
        </button>
        <span className="sql__toggle">{open ? "收起 ▴" : "展开 ▾"}</span>
      </div>
      {open && (
        <Highlight code={sql} language="sql" theme={themes.vsDark}>
          {({ className, style, tokens, getLineProps, getTokenProps }) => (
            <pre className={`sql__code ${className}`} style={style}>
              {tokens.map((line, i) => (
                <div key={i} {...getLineProps({ line })}>
                  <span className="sql__lineno">{i + 1}</span>
                  {line.map((token, k) => (
                    <span key={k} {...getTokenProps({ token })} />
                  ))}
                </div>
              ))}
            </pre>
          )}
        </Highlight>
      )}
    </div>
  );
}
