import React from "react";

const DIFF_CLASS = {
  Easy: "badge-easy",
  Medium: "badge-medium",
  Hard: "badge-hard",
};

/**
 * Displays the top recommended problems.
 * mode_toggle: lets the user switch between 'interview' and 'weakness' bias.
 * on_mode_change: callback so DashboardPage can re-fetch recommendations.
 */
function RecommendationWidget({ recommendations, mode, on_mode_change, loading }) {
  console.log(`loading value=${loading}`);
  console.log(`recommendations.length=${recommendations.length}`);
  return (
    <div className="dash-card dash-card-wide">
      <div className="flex items-center justify-between mb-3">
        <p className="dash-card-title mb-0">Next problems</p>
        <div className="mode-toggle" style={{ width: "auto", gap: "0.4rem" }}>
          <button
            id="rec-mode-interview"
            className={`mode-btn${mode === "interview" ? " active" : ""}`}
            onClick={() => on_mode_change("interview")}
          >
            🎯 Interview
          </button>
          <button
            id="rec-mode-weakness"
            className={`mode-btn${mode === "weakness" ? " active" : ""}`}
            onClick={() => on_mode_change("weakness")}
          >
            💡 Weakness
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex flex-col gap-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-16 rounded-xl" />
          ))}
        </div>
      )}

      {!loading && (!recommendations || recommendations.length === 0) && (
        <p className="text-sm text-gray-500">
          No recommendations yet — sync your profile first.
        </p>
      )}

      {!loading && recommendations && recommendations.length > 0 && (
        <div className="flex flex-col gap-2">
          {recommendations.map((rec) => (
            <a
              key={rec.title_slug}
              href={`https://leetcode.com/problems/${rec.title_slug}/`}
              target="_blank"
              rel="noopener noreferrer"
              className="rec-card no-underline"
              id={`rec-${rec.title_slug}`}
            >
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-semibold text-white">{rec.title}</span>
                <span className={DIFF_CLASS[rec.difficulty] || "badge-medium"}>
                  {rec.difficulty}
                </span>
                <span className="text-xs text-gray-500 ml-auto">
                  {rec.acceptance_rate}% acceptance
                </span>
              </div>
              <div className="flex flex-wrap gap-1">
                {rec.topics.slice(0, 4).map((t) => (
                  <span
                    key={t}
                    className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-gray-400"
                  >
                    {t}
                  </span>
                ))}
              </div>
              <p className="text-xs text-violet-400 mt-0.5">{rec.rationale}</p>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

export default RecommendationWidget;
