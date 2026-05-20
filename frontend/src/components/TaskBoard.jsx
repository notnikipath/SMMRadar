import React from "react";

export function TaskBoard({ topAuthors, alerts }) {
  return (
    <section className="board-grid">
      <div className="board-card">
        <h3>Top authors</h3>
        <div className="board-list">
          {topAuthors.length ? (
            topAuthors.map((author) => (
              <div className="board-item" key={author.author_id}>
                <div>
                  <strong>{author.author_name}</strong>
                  <p>{author.mentions} mentions</p>
                </div>
                <span>{author.engagement}</span>
              </div>
            ))
          ) : (
            <p className="muted">No author data yet.</p>
          )}
        </div>
      </div>

      <div className="board-card">
        <h3>Alert stream</h3>
        <div className="board-list">
          {alerts.length ? (
            alerts.map((alert) => (
              <div className="board-item" key={alert.alert_id}>
                <div>
                  <strong>{alert.severity}</strong>
                  <p>{alert.details}</p>
                </div>
                <span>{new Date(alert.created_at).toLocaleTimeString()}</span>
              </div>
            ))
          ) : (
            <p className="muted">No active alerts.</p>
          )}
        </div>
      </div>
    </section>
  );
}
