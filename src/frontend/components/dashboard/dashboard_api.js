/**
 * Centralised API helper for dashboard endpoints.
 * Reads the JWT from localStorage and optionally attaches X-LC-Session.
 */

const BASE = "http://localhost:5000";

function auth_headers(lc_session = null) {
  const token = localStorage.getItem("token");
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
  if (lc_session) {
    headers["X-LC-Session"] = lc_session;
  }
  return headers;
}

export async function get_account_status() {
  const res = await fetch(`${BASE}/api/dashboard/account/status`, {
    headers: auth_headers(),
  });
  return res.json();
}

export async function link_handle(handle) {
  const res = await fetch(`${BASE}/api/dashboard/account/link`, {
    method: "POST",
    headers: auth_headers(),
    body: JSON.stringify({ handle }),
  });
  return res.json();
}

export async function unlink_handle() {
  const res = await fetch(`${BASE}/api/dashboard/account/unlink`, {
    method: "POST",
    headers: auth_headers(),
  });
  return res.json();
}

export async function get_public_profile() {
  const res = await fetch(`${BASE}/api/dashboard/public/profile`, {
    headers: auth_headers(),
  });
  if (!res.ok) throw new Error((await res.json()).error);
  return res.json();
}

export async function sync_public_profile() {
  const res = await fetch(`${BASE}/api/dashboard/public/sync`, {
    method: "POST",
    headers: auth_headers(),
  });
  if (!res.ok) throw new Error((await res.json()).error);
  return res.json();
}

export async function get_public_recommendations(mode = "interview", top_n = 5) {
  const res = await fetch(
    `${BASE}/api/dashboard/public/recommendations?mode=${mode}&top_n=${top_n}`,
    { headers: auth_headers() }
  );
  if (!res.ok) throw new Error((await res.json()).error);
  return res.json();
}

export async function get_private_profile(lc_session) {
  const res = await fetch(`${BASE}/api/dashboard/private/profile`, {
    headers: auth_headers(lc_session),
  });
  if (!res.ok) throw new Error((await res.json()).error);
  return res.json();
}

export async function get_private_recommendations(lc_session, mode = "interview", top_n = 5) {
  const res = await fetch(
    `${BASE}/api/dashboard/private/recommendations?mode=${mode}&top_n=${top_n}`,
    { headers: auth_headers(lc_session) }
  );
  if (!res.ok) throw new Error((await res.json()).error);
  return res.json();
}
