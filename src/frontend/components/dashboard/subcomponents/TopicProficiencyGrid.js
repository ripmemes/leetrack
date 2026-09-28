import React from "react";

/**
 * Horizontal bar chart for topic-level solved counts.
 * Shows the top N topics sorted by solved count descending.
 */
function TopicProficiencyGrid({ topic_stats, max_display = 10 }) {
  if (!topic_stats || topic_stats.length === 0) {
    return (
      <div className="dash-card">
        <p className="dash-card-title">Topic proficiency</p>
        <p className="text-sm text-gray-500">No topic data available.</p>
      </div>
    );
  }

  const sorted = [...topic_stats]
    .sort((a, b) => b.solved - a.solved)
    .slice(0, max_display);

  const max_solved = sorted[0]?.solved || 1;

  return (
    <div className="dash-card" style={{ gridColumn: "span 2" }}>
      <p className="dash-card-title">Topic proficiency (top {sorted.length})</p>
      <div className="flex flex-col gap-2.5">
        {sorted.map(({ slug, name, solved }) => {
          const pct = Math.round((solved / max_solved) * 100);
          return (
            <div key={slug} className="flex items-center gap-3">
              <span
                className="text-xs text-gray-400 w-36 shrink-0 truncate"
                title={name}
              >
                {name}
              </span>
              <div className="progress-track flex-1">
                <div
                  className="progress-fill"
                  style={{
                    width: `${pct}%`,
                    background: `linear-gradient(90deg, #c2410c, #fb923c)`,
                  }}
                />
              </div>
              <span className="text-xs text-gray-500 w-8 text-right shrink-0">
                {solved}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default TopicProficiencyGrid;
