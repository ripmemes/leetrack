import React from "react";

/**
 * Displays avatar, handle, global ranking and contest info.
 */
function ProfileHeaderCard({ profile }) {
  const { handle, real_name, avatar_url, ranking, contest_info } = profile;

  return (
    <div className="dash-card flex items-center gap-4">
      <img
        src={avatar_url || `https://ui-avatars.com/api/?name=${handle}&background=6d28d9&color=fff`}
        alt={handle}
        className="w-14 h-14 rounded-full ring-2 ring-emerald-500 flex-shrink-0"
      />
      <div className="min-w-0">
        <h2 className="text-lg font-bold text-white truncate">{real_name || handle}</h2>
        <p className="text-sm text-gray-400">@{handle}</p>
        <div className="flex items-center gap-3 mt-1.5 flex-wrap">
          <Stat label="Rank" value={ranking ? `#${ranking.toLocaleString()}` : "—"} />
          {contest_info && (
            <>
              <Stat label="Contest rating" value={Math.round(contest_info.rating)} />
              <Stat label="Contests" value={contest_info.attended} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="text-center">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-sm font-semibold text-black">{value}</div>
    </div>
  );
}

export default ProfileHeaderCard;
