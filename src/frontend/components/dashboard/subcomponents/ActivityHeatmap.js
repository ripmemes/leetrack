import React, { useMemo } from "react";

/**
 * GitHub-style submission heatmap.
 * calendar prop: { "1690000000": 3, ... }  (Unix timestamp -> count)
 */
function ActivityHeatmap({ calendar }) {
  const weeks = useMemo(() => build_weeks(calendar), [calendar]);

  if (!calendar || Object.keys(calendar).length === 0) {
    return (
      <div className="dash-card dash-card-wide">
        <p className="dash-card-title">Activity</p>
        <p className="text-sm text-gray-500">No submission data available.</p>
      </div>
    );
  }

  return (
    <div className="dash-card dash-card-wide overflow-x-auto">
      <p className="dash-card-title">Submission activity (last year)</p>
      <div className="flex gap-1" style={{ minWidth: "max-content" }}>
        {weeks.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-1">
            {week.map((cell, di) => (
              <div
                key={di}
                className="heatmap-cell"
                style={{ background: cell_color(cell.count) }}
                title={cell.date ? `${cell.date}: ${cell.count} submissions` : ""}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2 mt-3 justify-end">
        <span className="text-xs text-gray-600">Less</span>
        {[0, 1, 3, 6, 10].map((v) => (
          <div
            key={v}
            className="heatmap-cell"
            style={{ background: cell_color(v) }}
          />
        ))}
        <span className="text-xs text-gray-600">More</span>
      </div>
    </div>
  );
}

/** Maps a submission count to an rgba color. */
function cell_color(count) {
  if (count === 0) return "rgba(0, 0, 0, 0.05)";       // Light gray empty tile
  if (count <= 2)  return "rgba(187, 247, 208, 1)";     // Emerald 200
  if (count <= 5)  return "rgba(74, 222, 128, 1)";      // Emerald 400
  if (count <= 9)  return "rgba(22, 163, 74, 1)";       // Emerald 600
  return "rgba(21, 128, 61, 1)";                       // Emerald 700 (solid dark green)
}

/** Converts the {timestamp: count} map into a 2-D weeks × days array. */
function build_weeks(calendar) {
  const today = new Date();
  const start = new Date(today);
  start.setFullYear(start.getFullYear() - 1);

  // Align start to the nearest Sunday
  start.setDate(start.getDate() - start.getDay());

  const date_map = {};
  for (const [ts, count] of Object.entries(calendar || {})) {
    const d = new Date(parseInt(ts, 10) * 1000);
    const key = d.toISOString().slice(0, 10);
    date_map[key] = (date_map[key] || 0) + count;
  }

  const weeks = [];
  let current = new Date(start);

  while (current <= today) {
    const week = [];
    for (let d = 0; d < 7; d++) {
      const key = current.toISOString().slice(0, 10);
      week.push({ date: key, count: date_map[key] || 0 });
      current.setDate(current.getDate() + 1);
    }
    weeks.push(week);
  }
  return weeks;
}

export default ActivityHeatmap;
