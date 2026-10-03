// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: 2026 The AxonOS Project / Denis Yermakou <connect@axonos.org>
//
// The example digest on pro.html and sample.html, rendered from the committed
// data the way a browser renders it, and held to the contract the product makes:
// an issue lists changes, and only changes. Every row must come from the week's
// change lists in data/weekly.json with its measured delta; the title must count
// the rows it shows; nothing may claim a human review; every link is GitHub's.
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const root = new URL("../", import.meta.url);
const read = (p) => readFileSync(new URL(p, root), "utf8");
const weekly = JSON.parse(read("data/weekly.json"));
const radar = JSON.parse(read("data/radar.json"));
const js = read("assets/offer.js");
let failures = 0;
const assert = (ok, msg) => { if (!ok) { failures++; console.error("FAIL", msg); } else console.log("ok  ", msg); };

for (const page of ["pro.html", "sample.html"]) {
  const dom = new JSDOM(read(page), { runScripts: "outside-only", url: "https://axonos-bci.github.io/axonos-community-radar/" + page });
  const w = dom.window;
  w.fetch = (u) => Promise.resolve({ ok: true, json: () => Promise.resolve(u.includes("weekly") ? weekly : radar) });
  w.eval(js);
  await new Promise((r) => setTimeout(r, 50));
  for (const fig of w.document.querySelectorAll("[data-digest]")) {
    const rows = [...fig.querySelectorAll("[data-digest-list] > li")];
    const n = Number(fig.getAttribute("data-rendered"));
    assert(n === rows.length && n > 0, `${page}: renders ${rows.length} rows and says ${n}`);
    const title = fig.querySelector("[data-digest-title]").textContent;
    assert(title.includes(`${n} change`), `${page}: the title counts the rows (${title})`);
    assert(!/analyst|checked by|reviewed/i.test(fig.textContent), `${page}: the engine digest claims no review`);
    for (const li of rows) {
      const name = li.querySelector("code").textContent;
      const what = li.querySelector(".what").textContent;
      if (li.classList.contains("up")) {
        const r = weekly.top_risers.find((x) => x.full_name === name);
        assert(r && what.includes(w.AxonOffer.stars(r.d7)), `${page}: ${name} is a riser with its measured delta`);
      } else if (li.classList.contains("fall")) {
        const r = weekly.top_fallers.find((x) => x.full_name === name);
        assert(r && r.d7 < 0 && what.includes(w.AxonOffer.stars(r.d7)), `${page}: ${name} is a faller with its measured delta`);
      } else if (li.classList.contains("new")) {
        assert(weekly.entrants.includes(name), `${page}: ${name} is a weekly entrant`);
      } else {
        assert(false, `${page}: ${name} has no change kind`);
      }
      const a = li.querySelector("a.ev");
      assert(a && /^https:\/\/github\.com\//.test(a.href), `${page}: ${name} links to its evidence on GitHub`);
    }
  }
}

// a week in which nothing on the list moved opens no issue, and says so
{
  const dom = new JSDOM(read("pro.html"), { runScripts: "outside-only" });
  const w = dom.window;
  const quiet = { ...weekly, top_risers: [], top_fallers: [], entrants: [] };
  w.fetch = (u) => Promise.resolve({ ok: true, json: () => Promise.resolve(u.includes("weekly") ? quiet : radar) });
  w.eval(js);
  await new Promise((r) => setTimeout(r, 50));
  const fig = w.document.querySelector("[data-digest]");
  assert(fig.getAttribute("data-rendered") === "0" && /no issue opened/i.test(fig.textContent), "a quiet week opens no issue");
}

if (failures) { console.error(`${failures} failure(s)`); process.exit(1); }
console.log("offer digest: every row is a real weekly change");
