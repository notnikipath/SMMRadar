import React from "react";

export function KpiCard({ title, value, hint, tone = "neutral" }) {
  return (
    <article className={`kpi-card tone-${tone}`}>
      <p className="kpi-title">{title}</p>
      <p className="kpi-value">{value}</p>
      <p className="kpi-hint">{hint}</p>
    </article>
  );
}
