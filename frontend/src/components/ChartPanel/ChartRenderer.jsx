import { useMemo } from "react";
import ReactECharts from "echarts-for-react";

/**
 * 把后端图表 JSON 规范化为 ECharts option。
 * chart 形如：
 *   { chartType, title?, xAxis?, series: [{ name, data }] }
 * 当 typeOverride 被传入时（用户在工具栏切换图表类型），覆盖 chart.chartType。
 *
 * onReady(echartsInstance) 在图表挂载完成后回调，用于导出 PNG。
 */
function buildOption(chart, typeOverride) {
  const type = typeOverride ?? chart.chartType ?? "bar";
  const baseTitle = {
    text: chart.title ?? "",
    left: "center",
    textStyle: { fontSize: 14, fontWeight: 600, color: "#111827" },
  };
  const baseLegend = { bottom: 0, type: "scroll" };
  const baseGrid   = { left: 40, right: 24, top: 56, bottom: 48, containLabel: true };

  if (type === "pie") {
    const data = chart.series?.[0]?.data ?? [];
    return {
      title: baseTitle,
      tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
      legend: { bottom: 0, type: "scroll" },
      series: [{
        name: chart.series?.[0]?.name ?? "占比",
        type: "pie",
        radius: ["35%", "65%"],
        center: ["50%", "50%"],
        avoidLabelOverlap: true,
        label: { formatter: "{b}\n{d}%" },
        data,
      }],
    };
  }

  if (type === "scatter") {
    const series = (chart.series ?? []).map((s) => ({
      name: s.name,
      type: "scatter",
      data: s.data,
      symbolSize: 10,
    }));
    return {
      title: baseTitle,
      tooltip: { trigger: "item" },
      legend: baseLegend,
      grid: baseGrid,
      xAxis: { type: "value", scale: true },
      yAxis: { type: "value", scale: true },
      series,
    };
  }

  // bar / line — 共用 xAxis(category)
  const series = (chart.series ?? []).map((s) => ({
    name: s.name,
    type,
    data: s.data,
    smooth: type === "line",
    barMaxWidth: 36,
    areaStyle: type === "line" ? { opacity: 0.15 } : undefined,
  }));

  return {
    title: baseTitle,
    tooltip: { trigger: "axis" },
    legend: baseLegend,
    grid: baseGrid,
    xAxis: {
      type: "category",
      data: chart.xAxis ?? [],
      axisLabel: { interval: 0, rotate: (chart.xAxis?.length ?? 0) > 8 ? 30 : 0 },
    },
    yAxis: { type: "value" },
    series,
  };
}

export default function ChartRenderer({ chart, typeOverride, onReady }) {
  const option = useMemo(() => buildOption(chart, typeOverride), [chart, typeOverride]);

  return (
    <ReactECharts
      option={option}
      notMerge
      lazyUpdate={false}
      style={{ width: "100%", height: "100%" }}
      opts={{ renderer: "canvas" }}
      onChartReady={(inst) => onReady?.(inst)}
    />
  );
}
