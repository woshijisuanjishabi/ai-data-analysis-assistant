import { BarChart3, LineChart, PieChart, ChartScatter, Download, Sparkles } from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";

import { useStore }   from "../../store/index.js";
import { demoCharts } from "../../mock/data.js";

const TYPES = [
  { key: "bar",     label: "柱状", icon: BarChart3 },
  { key: "line",    label: "折线", icon: LineChart },
  { key: "pie",     label: "饼图", icon: PieChart },
  { key: "scatter", label: "散点", icon: ChartScatter },
];

export default function ChartToolbar({ getInstance }) {
  const chart        = useStore((s) => s.activeChart);
  const override     = useStore((s) => s.chartTypeOverride);
  const setOverride  = useStore((s) => s.setChartTypeOverride);
  const setChart     = useStore((s) => s.setActiveChart);
  const currentType  = override ?? chart?.chartType ?? "bar";

  const handleType = (t) => {
    if (!chart) {
      // 没有图表时点切换 → 加载演示数据
      setChart(demoCharts[t]);
      return;
    }
    setOverride(t === chart.chartType ? null : t);
  };

  const handleDemo = () => {
    const types = ["bar", "line", "pie", "scatter"];
    const t = types[Math.floor(Math.random() * types.length)];
    setChart(demoCharts[t]);
    toast.success(`已加载 ${t} 演示数据`);
  };

  const handleExport = () => {
    const inst = getInstance?.();
    if (!inst) {
      toast.error("当前没有可导出的图表");
      return;
    }
    try {
      const url = inst.getDataURL({
        type: "png",
        pixelRatio: 2,
        backgroundColor: "#ffffff",
      });
      const a = document.createElement("a");
      a.href = url;
      a.download = `${chart?.title || "chart"}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      toast.success("已导出 PNG");
    } catch (e) {
      toast.error("导出失败：" + e.message);
    }
  };

  return (
    <div className="ct">
      <div className="ct__group">
        {TYPES.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            className={clsx("ct__btn", { "ct__btn--active": currentType === key })}
            onClick={() => handleType(key)}
            title={`切换为${label}图`}
          >
            <Icon size={14} />
            <span>{label}</span>
          </button>
        ))}
      </div>
      <div className="ct__group ct__group--right">
        <button className="ct__btn ct__btn--ghost" onClick={handleDemo} title="加载演示数据">
          <Sparkles size={14} />
          <span>Demo</span>
        </button>
        <button
          className="ct__btn ct__btn--primary"
          onClick={handleExport}
          disabled={!chart}
          title="导出 PNG"
        >
          <Download size={14} />
          <span>导出</span>
        </button>
      </div>
    </div>
  );
}
