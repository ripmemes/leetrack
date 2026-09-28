import React from "react";

const TIERS = [
  { key: "easy",   label: "Easy",   color: "#4ade80", bg: "rgba(34,197,94,0.15)" },
  { key: "medium", label: "Medium", color: "#facc15", bg: "rgba(234,179,8,0.15)" },
  { key: "hard",   label: "Hard",   color: "#f87171", bg: "rgba(239,68,68,0.15)" },
];

/**
 * Segmented bar + counts for Easy / Medium / Hard solved problems.
 */
function DifficultyDistribution({ solved_stats }) {
  const total = solved_stats.total || 1; // avoid div/0

  return (
    <div className="dash-card">
      <p className="dash-card-title">Solved problems</p>

      <div className="flex items-end justify-center gap-2 mb-4">
        <span className="text-4xl font-bold text-white">{solved_stats.total}</span>
        <span className="text-gray-500 text-sm mb-1">solved</span>
      </div>

      {/* segmented bar */}
      <div className="flex rounded-full overflow-hidden h-3 mb-4">
        {TIERS.map(({ key, color }) => {
          const pct = (solved_stats[key] / total) * 100;
          return (
            <div
              key={key}
              style={{ width: `${pct}%`, background: color, opacity: 0.85 }}
              title={`${solved_stats[key]} ${key}`}
            />
          );
        })}
      </div>

      <div className="flex justify-around">
        {TIERS.map(({ key, label, color, bg }) => (
          <div key={key} className="text-center">
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{ background: bg, color }}
            >
              {label}
            </span>
            <p className="text-lg font-bold text-white mt-1">{solved_stats[key]}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default DifficultyDistribution;
