import React, { useState } from "react";
import { link_handle, unlink_handle } from "../dashboard_api";

/**
 * Card shown at the top of the dashboard.
 * Handles linking a public username OR injecting a private LC session cookie.
 * The session cookie is read from the browser extension and passed in via props.
 */
function AccountConnectCard({ handle, lc_session, on_handle_change, on_session_change }) {
  const [input_val, set_input_val] = useState(handle || "");
  const [loading, set_loading] = useState(false);
  const [error, set_error] = useState(null);
  const [msg, set_msg] = useState(null);

  const handle_link = async () => {
    if (!input_val.trim()) return;
    set_loading(true);
    set_error(null);
    try {
      await link_handle(input_val.trim());
      on_handle_change(input_val.trim());
      set_msg("Handle linked successfully.");
    } catch (e) {
      set_error("Failed to link handle.");
    } finally {
      set_loading(false);
    }
  };

  const handle_unlink = async () => {
    set_loading(true);
    try {
      await unlink_handle();
      on_handle_change(null);
      on_session_change(null);
      set_input_val("");
      set_msg("Handle unlinked.");
    } catch (e) {
      set_error("Failed to unlink.");
    } finally {
      set_loading(false);
    }
  };

  return (
    <div className="dash-card dash-card-wide">
      <p className="dash-card-title">LeetCode Account</p>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        {/* username input */}
        <div className="flex-1">
          <label className="text-xs text-gray-400 mb-1 block">Public username</label>
          <input
            id="lc-handle-input"
            type="text"
            value={input_val}
            onChange={(e) => set_input_val(e.target.value)}
            placeholder="e.g. john_doe"
            className="w-full bg-gray-50 border-gray-30 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-600 focus:outline-none focus:border-violet-500"
          />
        </div>

        <button
          id="lc-link-btn"
          onClick={handle_link}
          disabled={loading || !input_val.trim()}
          className="px-4 py-2 rounded-lg bg-orange-500 hover:bg-orange-60 disabled:opacity-40 text-sm font-semibold text-gray-900 transition-colors"
        >
          {handle ? "Update" : "Link"}
        </button>

        {handle && (
          <button
            id="lc-unlink-btn"
            onClick={handle_unlink}
            disabled={loading}
            className="px-4 py-2 rounded-lg border border-white/10 hover:border-red-500/50 text-sm text-gray-400 hover:text-red-400 transition-colors"
          >
            Unlink
          </button>
        )}
      </div>

      {/* Private session section */}
      <div className="mt-4 p-3 rounded-lg border border-dashed border-white/10">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold text-orange-400">Private mode</span>
          {lc_session && (
            <span className="text-xs text-green-400 bg-green-400/10 px-2 py-0.5 rounded-full">
              Session active
            </span>
          )}
        </div>
        <p className="text-xs text-gray-500 mb-2">
          Install the Leetrack extension to auto-inject your session cookie. Or paste it below manually.
        </p>
        <div className="flex gap-2">
          <input
            id="lc-session-input"
            type="password"
            value={lc_session || ""}
            onChange={(e) => on_session_change(e.target.value || null)}
            placeholder="LEETCODE_SESSION cookie value"
            className="flex-1 bg-gray-50 border-gray-300 border border-white/10 rounded-lg px-3 py-2 text-xs text-gray-900 placeholder-gray-600 focus:outline-none focus:border-violet-500"
          />
          {lc_session && (
            <button
              onClick={() => on_session_change(null)}
              className="text-xs text-gray-500 hover:text-red-400 px-2 transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
      {msg && <p className="mt-2 text-xs text-green-400">{msg}</p>}
    </div>
  );
}

export default AccountConnectCard;
