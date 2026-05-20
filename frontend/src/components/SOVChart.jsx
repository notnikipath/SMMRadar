import * as d3 from "d3";
import React, { useEffect, useMemo, useRef } from "react";

function toSovRows(raw) {
  const total = raw.reduce((acc, item) => acc + Number(item.mentions || 0), 0);
  return raw.map((item) => ({
    brand: item.brand,
    mentions: Number(item.mentions || 0),
    share: total > 0 ? (Number(item.mentions || 0) / total) * 100 : 0,
  }));
}

export function SOVChart({ competitors }) {
  const ref = useRef(null);
  const rows = useMemo(() => toSovRows(competitors || []), [competitors]);

  useEffect(() => {
    const root = ref.current;
    if (!root) {
      return;
    }

    const width = root.clientWidth || 620;
    const height = 260;
    const margin = { top: 18, right: 20, bottom: 40, left: 46 };

    const svg = d3.select(root).html("").append("svg").attr("width", width).attr("height", height);

    if (!rows.length) {
      svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", height / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "#5f5f5f")
        .text("No competitor data");
      return;
    }

    const x = d3
      .scaleBand()
      .domain(rows.map((row) => row.brand))
      .range([margin.left, width - margin.right])
      .padding(0.24);

    const y = d3.scaleLinear().domain([0, 100]).range([height - margin.bottom, margin.top]);

    svg
      .append("g")
      .selectAll("rect")
      .data(rows)
      .enter()
      .append("rect")
      .attr("x", (row) => x(row.brand))
      .attr("y", (row) => y(row.share))
      .attr("width", x.bandwidth())
      .attr("height", (row) => y(0) - y(row.share))
      .attr("rx", 10)
      .attr("fill", "#dc2626");

    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).tickSizeOuter(0));

    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(5).tickFormat((value) => `${value}%`).tickSizeOuter(0));
  }, [rows]);

  return <div className="chart" ref={ref} />;
}
