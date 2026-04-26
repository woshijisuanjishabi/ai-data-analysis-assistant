import { useRef } from "react";

import { useStore } from "../../store/index.js";
import ChartToolbar  from "./ChartToolbar.jsx";
import ChartRenderer from "./ChartRenderer.jsx";
import EmptyChart    from "./EmptyChart.jsx";

import "./ChartPanel.css";

export default function ChartPanel() {
  const chart    = useStore((s) => s.activeChart);
  const override = useStore((s) => s.chartTypeOverride);
  const instRef  = useRef(null);

  return (
    <div className="cp">
      <div className="cp__header">
        <span className="cp__title">可视化</span>
        <span className="cp__sub">{chart?.title ?? ""}</span>
      </div>
      <div className="cp__toolbar">
        <ChartToolbar getInstance={() => instRef.current} />
      </div>
      <div className="cp__body">
        {chart
          ? <ChartRenderer
              key={(chart.title ?? "") + "::" + (chart.chartType ?? "")}
              chart={chart}
              typeOverride={override}
              onReady={(inst) => (instRef.current = inst)}
            />
          : <EmptyChart />}
      </div>
    </div>
  );
}
