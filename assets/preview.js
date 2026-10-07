/* SPDX-License-Identifier: MIT
 * SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
 *
 * AxonOS Radar · the Radar PRO dashboard preview. Everything here runs on the
 * page's own markup: choosing an audience re-orders the modules and the key
 * figures, the customize sheet shows and hides modules, the sidebar finds and
 * highlights them. No network request, no storage. The figures are the sample
 * data the page declares.
 */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };
  var mods = $("#mods"), all = $$(".mod", mods);

  var KP = {
    cur: [["9", "implant programmes with people in them"], ["4", "of them with peer-reviewed results"], ["3", "consumer headsets sending raw EEG to a cloud"], ["12", "headline claims checked this month"]],
    bld: [["31", "open tools with device support verified in code"], ["7", "critical libraries quiet for over a year"], ["2", "standards moved this quarter"], ["46", "open engineering roles"]],
    inv: [["11", "rounds disclosed this quarter"], ["5", "capital filings not yet announced"], ["3", "programmes moved to recruiting"], ["2", "companies whose hiring turned clinical"]]
  };
  function kpis(p) {
    var box = $("#kp"); box.textContent = "";
    KP[p].forEach(function (k) { var d = document.createElement("div"), b = document.createElement("b"), s = document.createElement("span"); b.textContent = k[0]; s.textContent = k[1]; d.appendChild(b); d.appendChild(s); box.appendChild(d); });
  }
  function audience(p) {
    $$(".pv-who button").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-p") === p)); });
    var first = all.filter(function (m) { return (" " + m.getAttribute("data-who") + " ").indexOf(" " + p + " ") !== -1; });
    var rest = all.filter(function (m) { return first.indexOf(m) === -1; });
    first.concat(rest).forEach(function (m) { mods.appendChild(m); });
    kpis(p);
  }
  $$(".pv-who button").forEach(function (b) { b.addEventListener("click", function () { audience(b.getAttribute("data-p")); }); });

  /* customize: what the dashboard shows */
  function apply() {
    var shown = 0;
    $$(".cz-t input").forEach(function (c) {
      var k = c.getAttribute("data-t"), m = $("#m-" + k), s = $('.sb-i[data-k="' + k + '"]');
      if (m) m.classList.toggle("gone", !c.checked);
      if (s) s.classList.toggle("off", !c.checked);
      if (c.checked) shown++;
    });
    $("#mnEmpty").hidden = shown > 0;
  }
  $$(".cz-t input").forEach(function (c) { c.addEventListener("change", apply); });
  $("#czAll").addEventListener("click", function () { $$(".cz-t input").forEach(function (c) { c.checked = true; }); apply(); });
  $("#czNone").addEventListener("click", function () { $$(".cz-t input").forEach(function (c) { c.checked = false; }); apply(); });
  var sheet = $("#cz"), opener = $("#czOpen"), last = null;
  function openSheet() { last = document.activeElement; sheet.hidden = false; $("#czClose").focus(); document.body.classList.add("cz-on"); }
  function closeSheet() { sheet.hidden = true; document.body.classList.remove("cz-on"); if (last) last.focus(); }
  opener.addEventListener("click", openSheet);
  $("#czClose").addEventListener("click", closeSheet);
  sheet.addEventListener("click", function (ev) { if (ev.target === sheet) closeSheet(); });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && !sheet.hidden) closeSheet(); });
  $$(".cz-seg button").forEach(function (b) { b.addEventListener("click", function () { $$(".cz-seg button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); }); }); });

  /* sidebar: find and highlight */
  $$(".sb-i").forEach(function (a) {
    a.addEventListener("click", function (ev) {
      var m = $("#m-" + a.getAttribute("data-k"));
      if (!m) return;
      ev.preventDefault();
      if (m.classList.contains("gone")) { var c = $('.cz-t input[data-t="' + a.getAttribute("data-k") + '"]'); if (c) { c.checked = true; apply(); } }
      $$(".sb-i").forEach(function (x) { x.classList.toggle("on", x === a); });
      $$(".mod.hit").forEach(function (x) { x.classList.remove("hit"); });
      m.classList.add("hit");
      m.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
      setTimeout(function () { m.classList.remove("hit"); }, 1800);
    });
  });
  $("#sbFind").addEventListener("input", function (ev) {
    var q = ev.target.value.trim().toLowerCase();
    $$(".sb-i").forEach(function (a) { a.hidden = q && a.textContent.toLowerCase().indexOf(q) === -1; });
  });


  /* count-up: the pulse figures arrive, they do not just sit there */
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  function countUp(el) {
    var raw = el.getAttribute("data-to"), m = raw.match(/^([^0-9]*)([0-9][0-9,.]*)(.*)$/);
    if (!m || reduce) return;
    var pre = m[1], num = parseFloat(m[2].replace(/,/g, "")), post = m[3], dec = (m[2].split(".")[1] || "").length, comma = m[2].indexOf(",") !== -1, t0 = null;
    function fmt(v) { var s = v.toFixed(dec); if (comma) s = Number(s).toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec }); return pre + s + post; }
    function tick(ts) { if (!t0) t0 = ts; var p = Math.min(1, (ts - t0) / 1200), e = 1 - Math.pow(1 - p, 3); el.textContent = fmt(num * e); if (p < 1) requestAnimationFrame(tick); }
    requestAnimationFrame(tick);
    setTimeout(function () { el.textContent = raw; }, 1500);  /* the true figure, whatever the frame rate */
  }
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (x) { if (x.isIntersecting) { countUp(x.target); io.unobserve(x.target); } }); }, { threshold: .6 });
    $$(".cu").forEach(function (el) { io.observe(el); });
  }

  /* device database: filter by type */
  $$(".dbf button").forEach(function (b) {
    b.addEventListener("click", function () {
      var f = b.getAttribute("data-df");
      $$(".dbf button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      $$(".dbt .tr[data-dt]").forEach(function (r) { r.classList.toggle("hid", f !== "all" && r.getAttribute("data-dt") !== f); });
    });
  });

  /* compare: any two companies, sample data */
  var CO = {
    "Arbor Neural": { Modality: "Intracortical", Stage: "Feasibility", Channels: "1,024", Trials: "2", Approvals: "IDE", Raised: "$310M", Roles: "42" },
    "Quill Bionics": { Modality: "ECoG", Stage: "Pivotal preparation", Channels: "4,096", Trials: "3", Approvals: "510(k)", Raised: "$255M", Roles: "27" },
    "Veyra Labs": { Modality: "Endovascular", Stage: "Feasibility", Channels: "16", Trials: "1", Approvals: "Breakthrough", Raised: "$145M", Roles: "9" },
    "Halden Neurotech": { Modality: "EEG", Stage: "Commercial", Channels: "8", Trials: "1", Approvals: "510(k)", Raised: "$60M", Roles: "18" }
  };
  var A = $("#cmpA"), B = $("#cmpB");
  if (A && B) {
    Object.keys(CO).forEach(function (n, i) { A.appendChild(new Option(n, n, i === 0, i === 0)); B.appendChild(new Option(n, n, i === 1, i === 1)); });
    var num = function (s) { return parseFloat(String(s).replace(/[^0-9.]/g, "")) || 0; };
    var draw = function () {
      var a = CO[A.value], b = CO[B.value], out = $("#cmpT"); out.textContent = "";
      var head = document.createElement("div"); ["", A.value, B.value].forEach(function (t) { var s = document.createElement(t ? "b" : "span"); s.textContent = t; head.appendChild(s); }); out.appendChild(head);
      Object.keys(a).forEach(function (k) {
        var row = document.createElement("div"), l = document.createElement("span"), x = document.createElement("b"), y = document.createElement("b");
        l.textContent = k; x.textContent = a[k]; y.textContent = b[k];
        if (["Channels", "Trials", "Raised", "Roles"].indexOf(k) !== -1 && num(a[k]) !== num(b[k])) (num(a[k]) > num(b[k]) ? x : y).className = "win";
        row.appendChild(l); row.appendChild(x); row.appendChild(y); out.appendChild(row);
      });
    };
    A.addEventListener("change", draw); B.addEventListener("change", draw); draw();
  }

  audience("inv");
  apply();
})();
