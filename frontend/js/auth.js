// Google-only login gate. Renders a full-screen "Sign in with Google" card when
// auth is enforced and there's no valid session; on success it stores the app
// session token and hands control back to the app.
import { api, getSession, setSession } from "./api.js";
import { h } from "./ui.js";

// Decode the exp from our session token (base64url(payload).sig) without verifying
// the signature — the server verifies for real; this only avoids showing the app
// then bouncing on a known-expired token.
export function sessionValid() {
  const tok = getSession();
  if (!tok || !tok.includes(".")) return false;
  try {
    const body = tok.split(".")[0].replace(/-/g, "+").replace(/_/g, "/");
    const payload = JSON.parse(atob(body + "=".repeat((4 - (body.length % 4)) % 4)));
    return typeof payload.exp === "number" && payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

let _gisLoaded = null;
function loadGis() {
  if (_gisLoaded) return _gisLoaded;
  _gisLoaded = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = "https://accounts.google.com/gsi/client";
    s.async = true;
    s.onload = resolve;
    s.onerror = () => reject(new Error("Could not load Google Sign-In"));
    document.head.appendChild(s);
  });
  return _gisLoaded;
}

// Show the login screen as a full-screen overlay. The app shell (#app) is hidden,
// not destroyed, so render()'s cached nodes survive; on success we remove the
// overlay, reveal #app, and hand back to onSuccess().
export function showLogin(clientId, onSuccess) {
  const appEl = document.getElementById("app");
  appEl.style.display = "none";
  const existing = document.getElementById("login-overlay");
  if (existing) existing.remove();

  const err = h("div.banner-err", { style: "display:none" });
  const btnHolder = h("div", { style: "display:flex;justify-content:center;min-height:44px" });

  const overlay = h("div.login-screen", { id: "login-overlay" }, [
    h("div.login-card", null, [
      h("div.login-brand", null, [h("span", { style: "font-size:34px" }, "🏞️"), "Landseer"]),
      h("p.login-sub", null, "Land search & evaluation — Vellore"),
      err,
      btnHolder,
      h("p.login-foot", null, "Access is restricted to authorized Google accounts."),
    ]),
  ]);
  document.body.appendChild(overlay);

  const finish = () => {
    overlay.remove();
    appEl.style.display = "";
    onSuccess();
  };
  const fail = (msg) => {
    err.textContent = msg;
    err.style.display = "block";
  };

  loadGis()
    .then(() => {
      if (!window.google || !clientId) {
        fail("Sign-in is unavailable (missing Google client configuration).");
        return;
      }
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (resp) => {
          try {
            const { session } = await api.createSession(resp.credential);
            setSession(session);
            finish();
          } catch (e) {
            fail(e.status === 403 ? "This Google account isn't allowed." : `Sign-in failed: ${e.message}`);
          }
        },
      });
      window.google.accounts.id.renderButton(btnHolder, {
        theme: "outline",
        size: "large",
        text: "signin_with",
        shape: "pill",
      });
    })
    .catch((e) => fail(e.message));
}

export function signOut() {
  setSession("");
  location.reload();
}
