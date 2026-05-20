import * as d3 from "d3";
import React, { useEffect, useRef } from "react";

export function TrendChart({ points }) {
  const ref = useRef(null);

  useEffect(() => {
    const root = ref.current;
    if (!root) {
      return;
    }

    const width = root.clientWidth || 620;
    const height = 260;
    const margin = { top: 18, right: 18, bottom: 34, left: 40 };

    const data = (points || []).map((point) => ({
      ts: new Date(point.ts_hour),
      mentions: Number(point.mentions || 0),
    }));

    const svg = d3.select(root).html("").append("svg").attr("width", width).attr("height", height);

    if (!data.length) {
      svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", height / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "#5f5f5f")
        .text("No dynamics yet");
      return;
    }

    const x = d3
      .scaleTime()
      .domain(d3.extent(data, (d) => d.ts))
      .range([margin.left, width - margin.right]);

    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d.mentions) || 1])
      .nice()
      .range([height - margin.bottom, margin.top]);

    const line = d3
      .line()
      .x((d) => x(d.ts))
      .y((d) => y(d.mentions))
      .curve(d3.curveCatmullRom.alpha(0.7));

    svg
      .append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#0f766e")
      .attr("stroke-width", 3)
      .attr("d", line);

    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(5).tickSizeOuter(0));

    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(4).tickSizeOuter(0));

    svg
      .selectAll("circle")
      .data(data)
      .enter()
      .append("circle")
      .attr("cx", (d) => x(d.ts))
      .attr("cy", (d) => y(d.mentions))
      .attr("r", 3.6)
      .attr("fill", "#ea580c");
  }, [points]);

  return <div className="chart" ref={ref} />;
}
