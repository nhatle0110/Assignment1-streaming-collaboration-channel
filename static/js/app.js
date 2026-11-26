"use strict";
/*
 * app.js: draws the page and handles what the user does. No network code here:
 * every request goes through `Api` (api.js), every change on screen comes from an
 * agent event (handleEvent). Text typed by users is always put in the page with
 * textContent (function h), never innerHTML, so it cannot inject HTML (XSS).
 */

const ERROR_TEXT = {
  UNKNOWN_MESSAGE_TYPE: "Unknown message type",
  INVALID_PAYLOAD: "Invalid request data",
  AUTH_FAILED: "Wrong username or password",
  ALREADY_LOGGED_IN: "This account is already logged in elsewhere",
  ALREADY_AUTHENTICATED: "You are already logged in",
  NOT_AUTHENTICATED: "Please log in first",
  NOT_CONNECTED: "Not connected to the server",
  SERVER_UNREACHABLE: "The server does not answer",
  TIMEOUT: "Timed out waiting for the server",
  USER_NOT_FOUND: "User not found",
  USER_OFFLINE: "User is offline",
  TRANSFER_NOT_FOUND: "Transfer not found",
};
const CONN_TEXT = {
  disconnected: "Disconnected", connecting: "Connecting…", established: "Handshake done",
  authenticated: "Connected", closing: "Closing…",
};
const FILE_TEXT = {
  incoming: "Waiting for you", offered: "Waiting for recipient", ready: "Ready",
  transferring: "Transferring", verifying: "Verifying", completed: "Completed ✓",
  rejected: "Rejected", failed: "Failed",
};
const FILE_DONE = new Set(["completed", "rejected", "failed"]);

const state = {
  me: null,
  conn: "disconnected",
  link: true,
  users: new Map(),     // online usernames -> {ip, port}
  convs: new Map(),     // "*" or username -> [{sender, text, ts}]
  transfers: new Map(), // file_id -> transfer
  net: {},
  active: "*",
};

const $ = (id) => document.getElementById(id);

/** Build a DOM node. Text is always set via textContent/append, never innerHTML (XSS-safe). */
function h(tag, props, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, "");
    else if (v !== false && v != null) el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid);
  return el;
}

const initials = (name) => (name || "?").slice(0, 2).toUpperCase();
const fmtTime = (ts) => new Date(ts * 1000).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
function fmtBytes(n) {
  if (n < 1024) return n + " B";
  if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
  if (n < 1073741824) return (n / 1048576).toFixed(1) + " MB";
  return (n / 1073741824).toFixed(2) + " GB";
}
const errText = (code) => ERROR_TEXT[code] || code;

/* ------------------------------------------------------------------ */
/* Toasts, banner, views                                              */
/* ------------------------------------------------------------------ */
function toast(text, info) {
  const el = h("div", { class: "toast" + (info ? " info" : ""), role: "alert" }, text);
  $("toasts").append(el);
  setTimeout(() => el.remove(), 5000);
}

function showView(app) {
  $("login-view").hidden = app;
  $("app-view").hidden = !app;
}

function renderBanner() {
  const b = $("banner");
  b.replaceChildren();
  if (!state.link) {
    b.className = "banner bad";
    b.append("Cannot reach the local agent — retrying…");
    b.hidden = false;
  } else if (state.me && state.conn === "disconnected") {
    b.className = "banner";
    b.append("Lost connection to the server.", h("button", { class: "btn ghost sm", type: "button", onclick: backToLogin }, "Back to login"));
    b.hidden = false;
  } else {
    b.hidden = true;
  }
}

function backToLogin() {
  state.me = null;
  state.users.clear();
  state.convs.clear();
  state.transfers.clear();
  state.net = {};
  state.active = "*";
  setLoginBusy(false);
  showView(false);
  renderBanner();
}

/* ------------------------------------------------------------------ */
/* Login                                                              */
/* ------------------------------------------------------------------ */
function setLoginBusy(busy) {
  $("login-btn").disabled = busy;
  $("login-btn").textContent = busy ? "Logging in…" : "Log in";
}

function showLoginError(text) {
  $("login-error").textContent = text;
  $("login-error").hidden = !text;
}

async function submitLogin(user, pass) {
  showLoginError("");
  setLoginBusy(true);
  try {
    const res = await Api.login(user, pass);
    if (!res.ok) {
      setLoginBusy(false);
      showLoginError(errText(res.code));
    }
  } catch (err) {
    setLoginBusy(false);
    showLoginError("Cannot reach the local agent");
  }
}

$("login-form").addEventListener("submit", (e) => {
  e.preventDefault();
  submitLogin($("login-user").value.trim(), $("login-pass").value);
});

$("logout-btn").addEventListener("click", async () => {
  try { await Api.logout(); } catch (err) { /* agent already gone: just leave */ }
  backToLogin();
});

/* ------------------------------------------------------------------ */
/* Conversations: "*" is the global chat, a username is a private chat */
/* ------------------------------------------------------------------ */
function convItems(key) {
  if (!state.convs.has(key)) state.convs.set(key, []);
  return state.convs.get(key);
}

function selectConv(key) {
  state.active = key;
  renderSidebar();
  renderHeader();
  renderMessages();
  $("text-input").focus();
}

function convButton(key, avatar, label) {
  return h("li", {}, h("button", {
    type: "button", class: key === state.active ? "act" : "", onclick: () => selectConv(key),
    "aria-current": key === state.active ? "true" : false,
  }, h("span", { class: "av" }, avatar), h("span", { class: "name" }, label),
  key !== "*" ? h("span", { class: "dot", title: "online" }) : null));
}

function renderSidebar() {
  $("channel-list").replaceChildren(convButton("*", "#", "Global chat"));
  const names = [...state.users.keys()].filter((n) => n !== state.me).sort((a, b) => a.localeCompare(b));
  $("user-list").replaceChildren(...names.map((n) => convButton(n, initials(n), n)));
  $("self-avatar").textContent = initials(state.me);
  $("self-name").textContent = state.me || "";
}

function renderHeader() {
  const priv = state.active !== "*";
  $("conv-title").textContent = priv ? "@ " + state.active : "# Global chat";
  const connected = state.conn === "authenticated" && state.link;
  $("pill-conn").textContent = (connected ? "● " : "○ ") + (CONN_TEXT[state.conn] || state.conn);
  $("pill-conn").className = "pill " + (connected ? "ok" : "bad");
  $("text-input").disabled = !connected;
  $("send-btn").disabled = !connected;
  $("attach-btn").disabled = !connected || !priv;
  $("attach-btn").title = priv ? "Send a file to " + state.active : "Select a user to send a file";
}

function renderMessages() {
  const box = $("messages");
  const items = convItems(state.active);
  const stick = box.scrollHeight - box.scrollTop - box.clientHeight < 60 || !box.children.length;
  if (!items.length) {
    box.replaceChildren(h("div", { class: "empty" }, "No messages yet."));
    return;
  }
  box.replaceChildren(...items.map((it) => {
    const mine = it.sender === state.me;
    return h("div", { class: "m" + (mine ? " mine" : "") }, h("div", { class: "av" }, initials(it.sender)),
      h("div", {}, h("div", { class: "meta" }, it.sender + " · " + fmtTime(it.ts)), h("div", { class: "bubble" }, it.text)));
  }));
  if (stick) box.scrollTop = box.scrollHeight;
}

function addMessage(key, msg) {
  convItems(key).push(msg);
  if (key === state.active) renderMessages();
}

/* ------------------------------------------------------------------ */
/* Sending messages and files                                         */
/* ------------------------------------------------------------------ */
$("composer").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("text-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  const target = state.active;
  try {
    const res = await Api.send(target, text);
    if (!res.ok) return toast(errText(res.code));
    addMessage(target, { sender: state.me, text, ts: Date.now() / 1000 }); // server does not echo our own messages
  } catch (err) {
    toast("Could not send: cannot reach the local agent");
  }
});

$("attach-btn").addEventListener("click", () => $("file-input").click());
$("file-input").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  const target = state.active;
  try {
    const res = await Api.offerFile(target, file);
    if (!res.ok) return toast(errText(res.code));
    if (!state.transfers.has(res.file_id)) { // the agent's first "file" event may already have created it
      upsertTransfer({ file_id: res.file_id, direction: "send", peer: target, filename: file.name, size_bytes: file.size, state: "offered" });
      renderTransfers();
    }
  } catch (err) {
    toast("Could not send the file: cannot reach the local agent");
  }
});

/* ------------------------------------------------------------------ */
/* File transfers (progress bars in the right panel)                  */
/* ------------------------------------------------------------------ */
function upsertTransfer(data) {
  let t = state.transfers.get(data.file_id);
  if (!t) {
    t = { file_id: data.file_id, transferred_bytes: 0, size_bytes: 0 };
    state.transfers.set(t.file_id, t);
  }
  Object.assign(t, Object.fromEntries(Object.entries(data).filter(([, v]) => v != null)));
  return t;
}

function fileCard(t) {
  const done = FILE_DONE.has(t.state);
  const pct = t.size_bytes ? Math.min(100, Math.floor((t.transferred_bytes / t.size_bytes) * 100)) : 0;
  const bad = t.state === "failed" || t.state === "rejected";
  const barCls = t.state === "completed" ? "done" : bad ? "fail" : "";
  const stCls = t.state === "completed" ? "st-ok" : bad ? "st-bad" : "st-wait";
  const arrow = (t.direction === "send" ? "↑ " : "↓ ") + t.peer;
  return h("div", { class: "card", "data-file": t.file_id },
    h("div", { class: "fname" }, t.filename),
    h("div", { class: "frow" }, h("span", {}, fmtBytes(t.size_bytes) + " · " + arrow), h("span", {}, t.state === "transferring" ? pct + "%" : "")),
    h("div", { class: "bar " + barCls, role: "progressbar", "aria-valuenow": pct, "aria-valuemin": 0, "aria-valuemax": 100 },
      h("i", { style: "width:" + (t.state === "completed" ? 100 : pct) + "%" })),
    h("div", { class: "frow" }, h("span", { class: stCls }, FILE_TEXT[t.state] || t.state)),
    t.state === "incoming" ? h("div", { class: "fact" },
      h("button", { class: "btn sm", type: "button", onclick: () => respond(t, true) }, "Accept"),
      h("button", { class: "btn ghost sm", type: "button", onclick: () => respond(t, false) }, "Reject")) : null);
}

function patchTransfer(t) {
  const el = document.querySelector('[data-file="' + CSS.escape(t.file_id) + '"]');
  if (el) el.replaceWith(fileCard(t));
  else renderTransfers();
}

function renderTransfers() {
  const list = [...state.transfers.values()].reverse();
  $("transfer-list").replaceChildren(...(list.length ? list.map(fileCard) : [h("div", { class: "small" }, "No files yet.")]));
}

async function respond(t, accepted) {
  try {
    const res = await Api.respondFile(t.file_id, accepted);
    if (!res.ok) return toast(errText(res.code));
    t.state = accepted ? "ready" : "rejected";
    patchTransfer(t);
  } catch (err) {
    toast("Cannot reach the local agent");
  }
}

/* ------------------------------------------------------------------ */
/* Network status card                                                */
/* ------------------------------------------------------------------ */
function renderNet() {
  const net = state.net;
  const row = (k, v) => h("div", { class: "row" }, h("span", {}, k), h("span", {}, v));
  $("net-card").replaceChildren(
    row("State", CONN_TEXT[state.conn] || state.conn),
    row("RTT", net.rtt_ms != null ? Math.round(net.rtt_ms) + " ms" : "—"),
    row("Timeout", net.timeout_ms != null ? Math.round(net.timeout_ms) + " ms" : "—"),
    row("Resent", net.resent != null ? (net.resent * 100).toFixed(1) + "%" : "—"),
    row("cwnd", net.cwnd != null ? net.cwnd + " packets" : "—"),
  );
}

/* ------------------------------------------------------------------ */
/* Events from the agent                                              */
/* ------------------------------------------------------------------ */
function handleEvent(ev) {
  switch (ev.type) {
    case "conn":
      state.conn = ev.state;
      if (ev.state === "disconnected" && !state.me) setLoginBusy(false);
      break;
    case "net":
      Object.assign(state.net, ev);
      break;
    case "auth_ack":
      setLoginBusy(false);
      if (ev.success) {
        state.me = ev.username;
        showView(true);
        selectConv("*");
      } else {
        showLoginError(errText(ev.error));
      }
      break;
    case "user_list":
      state.users.clear();
      ev.users.forEach((u) => state.users.set(u.username, { ip: u.ip, port: u.port }));
      break;
    case "presence":
      if (ev.status === "online") state.users.set(ev.username, {});
      else state.users.delete(ev.username);
      break;
    case "msg":
      addMessage(ev.target === "*" ? "*" : ev.sender === state.me ? ev.target : ev.sender, { sender: ev.sender, text: ev.text, ts: ev.timestamp });
      break;
    case "file_incoming":
      upsertTransfer({ file_id: ev.file_id, direction: "recv", peer: ev.sender, filename: ev.filename, size_bytes: ev.size_bytes, state: "incoming" });
      renderTransfers();
      toast(ev.sender + " wants to send " + ev.filename, true);
      break;
    case "file": {
      const isNew = !state.transfers.has(ev.file_id);
      const t = upsertTransfer({ file_id: ev.file_id, direction: ev.direction, peer: ev.peer, filename: ev.filename, size_bytes: ev.size_bytes, state: ev.state, transferred_bytes: ev.transferred_bytes });
      if (isNew) renderTransfers();
      else patchTransfer(t);
      break;
    }
    case "error":
      toast(errText(ev.code));
      break;
  }
}

function handleEvents(events) {
  events.forEach(handleEvent);
  renderBanner();
  if (state.me) {
    renderSidebar();
    renderHeader();
    renderNet();
  }
}

/* ------------------------------------------------------------------ */
/* Start                                                              */
/* ------------------------------------------------------------------ */
renderNet();
renderTransfers();
Api.startEvents(handleEvents, (up) => {
  if (state.link === up) return;
  state.link = up;
  renderBanner();
  if (state.me) renderHeader();
});
