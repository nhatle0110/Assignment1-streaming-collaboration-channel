"use strict";
/*
 * api.js: the only place where the page talks to the network. It sends HTTP
 * requests to this user's agent (apps/chatapp.py), which speaks CCP to the server.
 *
 *   POST /api/login         {username, password}   -> {ok}; the result comes as an "auth_ack" event
 *   POST /api/send          {target, text}         -> {ok}   (target "*" = everyone)
 *   POST /api/file/offer    the file's bytes, headers X-Target / X-Filename -> {ok, file_id}
 *   POST /api/file/respond  {file_id, accepted}    -> {ok}
 *   POST /api/logout        {}                     -> {ok}
 *   POST /api/events        {since}                -> {events, next}  (long polling)
 * On error the reply is {ok: false, code}.
 *
 * Events (objects with a "type"):
 *   conn          {state: connecting|established|authenticated|closing|disconnected, reason?}
 *   auth_ack      {success, username, error}
 *   user_list     {users: [{username, ip, port}]}
 *   presence      {username, status: online|offline}
 *   msg           {sender, target, text, timestamp}      (timestamp in Unix seconds)
 *   file_incoming {file_id, sender, filename, size_bytes, sha256}
 *   file          {file_id, direction: send|recv, peer, filename, size_bytes, transferred_bytes,
 *                  state: offered|incoming|ready|transferring|verifying|completed|rejected|failed}
 *   error         {code}
 *   net           {rtt_ms, timeout_ms, resent, cwnd}          once a second
 */

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const Api = (() => {
  async function post(path, body) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return res.json();
  }

  return {
    login: (username, password) => post("/api/login", { username, password }),
    send: (target, text) => post("/api/send", { target, text }),
    respondFile: (file_id, accepted) => post("/api/file/respond", { file_id, accepted }),
    logout: () => post("/api/logout", {}),
    async offerFile(target, file) {
      const res = await fetch("/api/file/offer", {
        method: "POST",
        headers: {
          "Content-Type": "application/octet-stream",
          "X-Target": encodeURIComponent(target),
          "X-Filename": encodeURIComponent(file.name),
        },
        body: file,
      });
      return res.json();
    },
    /** Long-poll loop: onEvents(list) per batch; onLink(true|false) when the agent is (un)reachable. */
    startEvents(onEvents, onLink) {
      let since = 0;
      (async function loop() {
        for (;;) {
          try {
            const data = await post("/api/events", { since });
            since = data.next;
            onLink(true);
            if (data.events.length) onEvents(data.events);
          } catch (err) {
            onLink(false);
            await sleep(1000);
          }
        }
      })();
    },
  };
})();
