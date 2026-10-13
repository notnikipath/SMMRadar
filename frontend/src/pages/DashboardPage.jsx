import React, { useEffect, useMemo, useState } from "react";

import { KpiCard } from "../components/KpiCard";
import { SOVChart } from "../components/SOVChart";
import { TaskBoard } from "../components/TaskBoard";
import { TrendChart } from "../components/TrendChart";

const gatewayUrl = (import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:31051").replace(/\/+$/, "");

async function fetchOverview() {
  const response = await fetch(`${gatewayUrl}/dashboard/overview`);
  if (!response.ok) {
    throw new Error(`Overview request failed: ${response.status}`);
  }
  return response.json();
}

async function triggerMonitorRun() {
  const response = await fetch(`${gatewayUrl}/workflow/monitor-run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      brand: "SMM Radar",
      collect: {
        platforms: ["vk", "telegram", "youtube", "twitter", "instagram"],
        keywords: ["SMM Radar", "support quality", "promo campaign"],
        hashtags: ["#smm", "#brand", "#reputation"],
        limit_per_platform: 5,
      },
      competitors: ["BrandPulse", "InsightFlow"],
    }),
  });
  if (!response.ok) {
    throw new Error(`Monitor run failed: ${response.status}`);
  }
  return response.json();
}

export function DashboardPage() {
  const [data, setData] = useState({
    summary: {},
    mention_dynamics: [],
    top_authors: [],
    geo_distribution: [],
    word_cloud: [],
    alerts: [],
    competitors: [],
  });
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);

  const reload = async () => {
    try {
      setStatus("loading");
      const payload = await fetchOverview();
      setData(payload);
      setStatus("live");
      setError(null);
    } catch (err) {
      setStatus("error");
      setError(err.message);
    }
  };

  useEffect(() => {
    reload();
  }, []);

  const runCycle = async () => {
    try {
      setStatus("running");
      await triggerMonitorRun();
      await reload();
    } catch (err) {
      setStatus("error");
      setError(err.message);
    }
  };

  const summary = data.summary || {};
  const totalMentions = Number(summary.total_mentions || 0);
  const crisis = Number(summary.crisis_probability || 0);
  const negativeRatio = Number(summary.negative_ratio || 0);
  const topPlatform = useMemo(() => {
    const items = Object.entries(summary.platforms || {}).sort((a, b) => b[1] - a[1]);
    return items[0] || ["n/a", 0];
  }, [summary]);

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">SMM Radar</p>
          <h1>Social intelligence</h1>
          <p className="sub">
            Unified monitoring across VK, Telegram, YouTube, Twitter, Instagram, Facebook, and Rutube.
          </p>
        </div>

        <div className="hero-actions">
          <button onClick={runCycle}>Run Monitoring Cycle</button>
          <button className="ghost" onClick={reload}>
            Refresh Dashboard
          </button>
          <p className="status">Status: {status}</p>
        </div>
      </header>

      {error ? <div className="error">{error}</div> : null}

      <section className="kpi-grid">
        <KpiCard title="Total Mentions" value={totalMentions.toLocaleString()} hint="All tracked social sources" tone="accent" />
        <KpiCard
          title="Crisis Probability"
          value={`${Math.round(crisis * 100)}%`}
          hint="Calculated from negative ratio + alerts"
          tone={crisis > 0.45 ? "warn" : "ok"}
        />
        <KpiCard
          title="Negative Ratio"
          value={`${Math.round(negativeRatio * 100)}%`}
          hint="Target below 35%"
          tone={negativeRatio > 0.35 ? "warn" : "ok"}
        />
        <KpiCard title="Top Source" value={`${topPlatform[0]}`} hint={`${topPlatform[1]} mentions`} tone="neutral" />
      </section>

      <section className="panel-grid">
        <article className="panel wide">
          <div className="panel-head">
            <h2>Mention Dynamics</h2>
            <span>Last 24h</span>
          </div>
          <TrendChart points={data.mention_dynamics || []} />
        </article>

        <article className="panel wide">
          <div className="panel-head">
            <h2>Share Of Voice</h2>
            <span>Brand vs competitors</span>
          </div>
          <SOVChart competitors={data.competitors || []} />
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>Geo Distribution</h2>
            <span>Mentions by city</span>
          </div>
          <div className="list">
            {(data.geo_distribution || []).slice(0, 8).map((item) => (
              <div className="list-item" key={item.location}>
                <strong>{item.location}</strong>
                <span>{item.mentions}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>Word Cloud Tokens</h2>
            <span>Most frequent</span>
          </div>
          <div className="token-cloud">
            {(data.word_cloud || []).slice(0, 24).map((word) => (
              <span key={word.token} style={{ fontSize: `${12 + Math.min(24, word.weight)}px` }}>
                {word.token}
              </span>
            ))}
          </div>
        </article>
      </section>

      <TaskBoard topAuthors={(data.top_authors || []).slice(0, 6)} alerts={(data.alerts || []).slice(0, 6)} />
    </div>
  );
}
