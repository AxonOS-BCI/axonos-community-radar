/* SPDX-License-Identifier: MIT
 * SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
 *
 * AxonOS Radar · the example digest on pro.html and sample.html, drawn from the
 * data this site publishes rather than typed into the page.
 *
 * 16.10.0 printed the digest as HTML: three rows labelled "real data" that were
 * right for one week and then wrong for every week after, and one of the three
 * was not a change at all — a repository that had been quiet for four years,
 * shown inside "3 changes this week" by a product that promises an issue only
 * when something changed. This builds the digest from data/weekly.json and
 * data/radar.json each time the page is opened:
 *
 *   ▲  a riser    — only from weekly.json top_risers, with its measured delta
 *   ＋  an entrant — only from weekly.json entrants, matched by a field watch
 *   ↓  a faller   — only from weekly.json top_fallers, with its measured delta
 *
 * Nothing quiet, nothing inferred, and no analyst: this is what the engine
 * opens on its own. A release is mentioned only when radar.json records one
 * inside the week. Every string from the data goes in through textContent, and
 * every link must be a github.com URL. If the data cannot be read, the window
 * says so, with no numbers.
 */
(function () {
  "use strict";

  function safeGithub(u) {
    return typeof u === "string" && /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/.test(u) ? u : null;
  }
  function day(iso) {
    var d = new Date(iso);
    if (isNaN(d)) return "";
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });
  }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  /** "+13 stars", "−1 star": the sign and the unit, written properly. */
  function stars(d) {
    var n = Math.abs(d);
    return (d < 0 ? "\u2212" : "+") + n + (n === 1 ? " star" : " stars");
  }
  function clip(s, n) {
    s = (s || "").replace(/\s+/g, " ").trim();
    return s.length > n ? s.slice(0, n - 1).replace(/[ ,;:.-]+$/, "") + "…" : s;
  }

  /** The pure part: which rows the engine would open, from the data alone. */
  function selectRows(weekly, radar, watch, fieldWatch) {
    var byName = {};
    (radar.projects || []).forEach(function (p) { byName[p.full_name] = p; });
    var onList = function (n) { return watch.indexOf(n) !== -1; };
    var risers = (weekly.top_risers || []).filter(function (r) { return onList(r.full_name) && r.d7 > 0 && byName[r.full_name]; })
      .sort(function (a, b) { return b.d7 - a.d7; });
    var fallers = (weekly.top_fallers || []).filter(function (r) { return onList(r.full_name) && r.d7 < 0 && byName[r.full_name]; })
      .sort(function (a, b) { return a.d7 - b.d7; });
    var entrants = (weekly.entrants || []).filter(function (n) {
      var p = byName[n];
      return p && ((p.facets && p.facets.modality) || []).indexOf(fieldWatch) !== -1;
    });
    var rows = [];
    if (risers[0]) rows.push({ kind: "up", name: risers[0].full_name, d7: risers[0].d7 });
    if (entrants[0]) rows.push({ kind: "new", name: entrants[0] });
    if (fallers[0]) rows.push({ kind: "fall", name: fallers[0].full_name, d7: fallers[0].d7 });
    for (var i = 1; rows.length < 3 && i < risers.length; i++) rows.push({ kind: "up", name: risers[i].full_name, d7: risers[i].d7 });
    rows.forEach(function (r) { r.project = byName[r.name]; });
    return rows;
  }

  function rowNode(r, weekly, fieldWatch) {
    var p = r.project, li = el("li", r.kind === "fall" ? "fall" : r.kind), glyph = { up: "▲", "new": "＋", fall: "↓" }[r.kind];
    li.appendChild(el("span", "glyph", glyph)).setAttribute("aria-hidden", "true");
    var box = el("div"), what = el("p", "what"), why = el("p", "why");
    what.appendChild(el("code", null, r.name));
    if (r.kind === "up" || r.kind === "fall") what.appendChild(document.createTextNode(" " + stars(r.d7) + " this week"));
    if (r.kind === "new") what.appendChild(document.createTextNode(" entered your “" + fieldWatch + "” field watch"));
    var reason = r.kind === "new"
      ? "New public project, BRS " + p.brs + ", first seen this week."
      : clip(p.description, 110);
    var rel = p.latest_release_at && p.latest_release_tag;
    if (r.kind === "up" && rel && p.latest_release_at >= weekly.span_from && p.latest_release_at <= weekly.span_to) {
      if (reason && !/[.!?…]$/.test(reason)) reason += ".";
      reason += (reason ? " " : "") + "Release " + p.latest_release_tag + " on " + day(p.latest_release_at) + ".";
    }
    why.textContent = reason;
    box.appendChild(what); box.appendChild(why); li.appendChild(box);
    var href = safeGithub(p.html_url);
    if (href) { var a = el("a", "ev", "evidence"); a.href = href; a.rel = "noopener"; li.appendChild(a); }
    return li;
  }

  function render(fig, weekly, radar) {
    var watch = (fig.getAttribute("data-watch") || "").split(/\s+/).filter(Boolean);
    var fieldWatch = fig.getAttribute("data-field-watch") || "EEG";
    var rows = selectRows(weekly, radar, watch, fieldWatch);
    var list = fig.querySelector("[data-digest-list]");
    list.textContent = "";
    rows.forEach(function (r) { list.appendChild(rowNode(r, weekly, fieldWatch)); });
    var n = rows.length;
    fig.querySelector("[data-digest-title]").textContent = n
      ? "Radar digest — " + n + (n === 1 ? " change" : " changes") + " this week"
      : "No change on your list this week — no issue opened";
    fig.querySelector("[data-digest-meta]").textContent =
      "Opened by the Radar engine after the weekly scan of " + day(weekly.span_to) + ".";
    fig.querySelector("[data-digest-tag]").textContent = "Live data · week to " + day(weekly.span_to);
    fig.setAttribute("data-rendered", String(n));
  }

  function failed(fig) {
    fig.querySelector("[data-digest-meta]").textContent =
      "This week's digest could not be read here. It is drawn from data/weekly.json on this site.";
    fig.setAttribute("data-rendered", "error");
  }

  function boot() {
    var figs = Array.prototype.slice.call(document.querySelectorAll("[data-digest]"));
    if (!figs.length || typeof fetch !== "function") return;
    Promise.all([
      fetch("./data/weekly.json", { cache: "no-store" }).then(function (r) { if (!r.ok) throw 0; return r.json(); }),
      fetch("./data/radar.json", { cache: "no-store" }).then(function (r) { if (!r.ok) throw 0; return r.json(); })
    ]).then(function (d) {
      figs.forEach(function (f) { render(f, d[0], d[1]); });
    }, function () { figs.forEach(failed); });
  }

  if (typeof window !== "undefined") window.AxonOffer = { selectRows: selectRows, render: render, stars: stars };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
