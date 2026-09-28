import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";

import "./dashboard.css";
import AccountConnectCard from "./subcomponents/AccountConnectCard";
import ProfileHeaderCard from "./subcomponents/ProfileHeaderCard";
import DifficultyDistribution from "./subcomponents/DifficultyDistribution";
import TopicProficiencyGrid from "./subcomponents/TopicProficiencyGrid";
import ActivityHeatmap from "./subcomponents/ActivityHeatmap";
import RecommendationWidget from "./subcomponents/RecommendationWidget";

import {
  get_account_status,
  get_public_profile,
  get_public_recommendations,
  get_private_profile,
  get_private_recommendations,
  sync_public_profile,
} from "./dashboard_api";

/**
 * Top-level dashboard page.
 * Orchestrates data fetching and passes slices down to sub-components.
 * lc_session (LEETCODE_SESSION cookie) is held only in React state — never persisted.
 */
function DashboardPage({ logged }) {
  const navigate = useNavigate();

  const [handle, set_handle] = useState(null);
  const [lc_session, set_lc_session] = useState(null); // never stored to localStorage
  const [profile, set_profile] = useState(null);
  const [recommendations, set_recommendations] = useState(null);
  const [rec_mode, set_rec_mode] = useState("interview");
  const [loading_profile, set_loading_profile] = useState(false);
  const [loading_recs, set_loading_recs] = useState(false);
  const [error, set_error] = useState(null);
  const [syncing, set_syncing] = useState(false);

  // Guard: redirect if not logged in
  useEffect(() => {
    if (!logged) navigate("/login");
  }, [logged, navigate]);

  // On mount: load the linked handle from the backend
  useEffect(() => {
    get_account_status()
      .then((data) => set_handle(data.handle || null))
      .catch(() => {});
  }, []);

  // Re-fetch profile whenever handle or session changes
  const fetch_profile = useCallback(async () => {
    if (!handle) {
      set_profile(null);
      set_recommendations(null);
      return;
    }
    set_loading_profile(true);
    set_error(null);
    try {
      const data = lc_session
        ? await get_private_profile(lc_session)
        : await get_public_profile();
      set_profile(data);
    } catch (e) {
      set_error(e.message || "Failed to fetch profile.");
    } finally {
      set_loading_profile(false);
    }
  }, [handle, lc_session]);

  useEffect(() => {
    fetch_profile();
  }, [fetch_profile]);

  // Re-fetch recommendations when mode or profile changes
  const fetch_recs = useCallback(async () => {
    if (!handle) return;
    set_loading_recs(true);
    try {
      const data = lc_session
        ? await get_private_recommendations(lc_session, rec_mode)
        : await get_public_recommendations(rec_mode);
      set_recommendations(data);
    } catch (e) {
      set_recommendations(null);
    } finally {
      set_loading_recs(false);
    }
  }, [handle, lc_session, rec_mode]);

  useEffect(() => {
    fetch_recs();
  }, [fetch_recs]);

  const handle_sync = async () => {
    if (!handle) return;
    set_syncing(true);
    try {
      const data = await sync_public_profile();
      set_profile(data);
      await fetch_recs();
    } catch (e) {
      set_error("Sync failed.");
    } finally {
      set_syncing(false);
    }
  };

  const is_private = Boolean(lc_session);

  return (
    <main className="dashboard-page">
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        {/* header row */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Dashboard</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {is_private ? "🔒 Private mode" : "🌐 Public mode"}
              {handle && <span className="ml-2 text-violet-400">@{handle}</span>}
            </p>
          </div>
          {handle && (
            <button
              id="dashboard-sync-btn"
              onClick={handle_sync}
              disabled={syncing}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-white/10 hover:border-violet-500/50 text-sm text-gray-400 hover:text-violet-300 transition-colors disabled:opacity-40"
            >
              {syncing ? "Syncing…" : "↻ Sync"}
            </button>
          )}
        </div>

        {error && (
          <div className="mb-4 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-sm text-red-400">
            {error}
          </div>
        )}

        <div className="dashboard-grid">
          {/* always shown */}
          <AccountConnectCard
            handle={handle}
            lc_session={lc_session}
            on_handle_change={set_handle}
            on_session_change={set_lc_session}
          />

          {/* skeleton while loading */}
          {loading_profile && !profile && (
            <>
              <div className="skeleton h-28 rounded-2xl" />
              <div className="skeleton h-28 rounded-2xl" />
              <div className="skeleton h-48 rounded-2xl dash-card-wide" />
            </>
          )}

          {/* loaded profile */}
          {profile && (
            <>
              <ProfileHeaderCard profile={profile} />
              <DifficultyDistribution solved_stats={profile.solved_stats} />
              <TopicProficiencyGrid topic_stats={profile.topic_stats} />
              <ActivityHeatmap calendar={profile.calendar} />
            </>
          )}

          {/* recommendations (always rendered when handle is set) */}
          {handle && (
            <RecommendationWidget
              recommendations={recommendations}
              mode={rec_mode}
              on_mode_change={set_rec_mode}
              loading={loading_recs}
            />
          )}

          {/* empty state */}
          {!handle && !loading_profile && (
            <div className="dash-card dash-card-wide text-center py-10">
              <p className="text-3xl mb-3">🔗</p>
              <p className="text-gray-300 font-semibold">Link your LeetCode account above</p>
              <p className="text-sm text-gray-500 mt-1">
                Enter your public username — no password required.
              </p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

export default DashboardPage;
