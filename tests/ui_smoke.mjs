// Functional UI smoke for the AxonOS Radar map (CI: frontend job).
// Boots the real index.html + assets/app.js inside jsdom against fixture
// data and asserts that rendering, filters, permalinks and licence markers
// actually work — not just that the file parses.
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const html = readFileSync("index.html", "utf8")
  // strip external <script src> tags — we eval app.js ourselves after stubbing
  .replace(/<script[^>]*src=[^>]*><\/script>/g, "");
const appJs = readFileSync("assets/app.js", "utf8");

const FIXTURE = {
  version: 3,
  generated_at: "2026-07-03T00:17:00+00:00",
  counts: { total: 4, active_30d: 3, new: 1, rising: 1 },
  projects: [
    { full_name: "AxonOS-org/axonos-kernel", html_url: "https://github.com/AxonOS-org/axonos-kernel",
      description: "", category: "Protocols & OS", language: "Rust", stars: 0, forks: 0,
      days_since_push: 2, active: true, is_new: true, rising: false, falling: false, stars_delta_7d: 0,
      evidence_tier: "", inclusion_reason: "", topics: [], quality_flags: {},
      license: "MIT", has_license: true, first_seen: "2026-07-01",
      ecosystem: true, ecosystem_role: "Real-time neural OS kernel", ecosystem_note: "Kernel core" },
    { full_name: "acme/rising", html_url: "https://github.com/acme/rising",
      description: "EEG decoder", category: "Decoding & ML", language: "Python",
      stars: 500, forks: 10, days_since_push: 1, active: true, is_new: false,
      rising: true, falling: false, stars_delta_7d: 12,
      evidence_tier: "L3_EXPLICIT_BCI", inclusion_reason: "topic:bci",
      topics: ["bci"], quality_flags: {}, license: "MIT", has_license: true, first_seen: "2026-06-01" },
    { full_name: "acme/faller", html_url: "https://github.com/acme/faller",
      description: "old toolkit", category: "Signal Processing", language: "C",
      stars: 300, forks: 5, days_since_push: 40, active: false, is_new: false,
      rising: false, falling: true, stars_delta_7d: -4,
      evidence_tier: "L2_NEURAL_SIGNAL", inclusion_reason: "keyword:eeg",
      topics: ["eeg"], quality_flags: {}, license: "Apache-2.0", has_license: true, first_seen: "2026-05-01" },
    { full_name: "solo/unlicensed", html_url: "https://github.com/solo/unlicensed",
      description: "no licence repo", category: "Protocols & OS", language: "Rust",
      stars: 50, forks: 1, days_since_push: 3, active: true, is_new: true,
      rising: false, falling: false, stars_delta_7d: 0,
      evidence_tier: "L1_CONTEXT_PLUS_NEURO", inclusion_reason: "context",
      topics: ["no-std"], quality_flags: {}, license: null, has_license: false, first_seen: "2026-07-01" },
    { full_name: "solo/unclear", html_url: "https://github.com/solo/unclear",
      description: "noassertion licence", category: "Privacy & Security", language: "Go",
      stars: 40, forks: 1, days_since_push: 9, active: true, is_new: false,
      rising: false, falling: false, stars_delta_7d: 1,
      evidence_tier: "L0_WEAK_ADJACENT", inclusion_reason: "weak",
      topics: ["privacy"], quality_flags: { possible_false_positive: true },
      license: "NOASSERTION", has_license: false, first_seen: "2026-06-20" },
  ],
  ecosystem: {
    owners: { "AxonOS-org": { login: "AxonOS-org", type: "Organization", name: "AxonOS",
      bio: "Open real-time neural OS", location: "Singapore", followers: 12, public_repos: 6,
      html_url: "https://github.com/AxonOS-org",
      members: [{ login: "denis-y", html_url: "https://github.com/denis-y" }] } },
    links: [{ a: "AxonOS-org/axonos-kernel", b: "AxonOS-org/axonos-protocol", weight: 2, shared: ["denis-y"] }],
    key_people: [{ login: "denis-y", reach: 3, repos: ["AxonOS-org/axonos-kernel","AxonOS-org/axonos-protocol","AxonOS-org/axonos-consent"] }],
    repo_count: 6
  },
  builders: [
    { owner: "acme", html_url: "https://github.com/acme", project_count: 2,
      total_stars: 800, active_projects_30d: 1, top_categories: ["Decoding & ML"],
      owner_type: "Organization", followers: 42 },
  ],
};
const WEEKLY = {
  generated_at: "2026-07-03T00:17:00+00:00",
  span_from: "2026-06-26T00:00:00+00:00", span_to: "2026-07-03T00:00:00+00:00",
  delta: { total: 5, total_stars: 120, active_30d: 2, rising: 1 },
  now: { total: 4, total_stars: 890, active_30d: 3, rising: 1 },
  top_risers: [{ full_name: "acme/rising", stars: 500, d7: 12 }],
  top_fallers: [{ full_name: "acme/faller", stars: 300, d7: -4 }],
  entrants: ["solo/unlicensed"],
};

const dom = new JSDOM(html, { url: "https://radar.test/", runScripts: "outside-only", pretendToBeVisual: true });
const { window } = dom;
// canvas stub: app.js grabs a 2d context at load; jsdom has no canvas impl.
const noop = () => {};
window.HTMLCanvasElement.prototype.getContext = () => new Proxy({}, { get: () => noop });
// fetch stub with our fixtures
window.fetch = (url) => {
  const u = String(url);
  if (u.indexOf("radar.json") >= 0) return Promise.resolve({ ok: true, json: () => Promise.resolve(FIXTURE) });
  if (u.indexOf("weekly.json") >= 0) return Promise.resolve({ ok: true, json: () => Promise.resolve(WEEKLY) });
  return Promise.resolve({ ok: false, json: () => Promise.reject(new Error("404")) });
};
window.eval(appJs);
await new Promise((r) => setTimeout(r, 60));   // let fetch microtasks flush

const $ = (id) => window.document.getElementById(id);
const q = (sel) => window.document.querySelectorAll(sel);
let passed = 0;
function assert(cond, name) {
  if (!cond) { console.error("✗ " + name); process.exit(1); }
  passed++; console.log("✓ " + name);
}

assert(q("#cards .pc").length === 5, "renders all fixture cards");
assert(window.document.body.textContent.indexOf("no licence") >= 0, "licence-missing marker shown");
assert(window.document.body.textContent.indexOf("licence unclear") >= 0, "NOASSERTION marker shown");
assert(!$("weekly").classList.contains("hidden") && $("weekly").textContent.indexOf("This week") >= 0,
       "weekly strip rendered from weekly.json");
assert($("weekly").querySelectorAll("a").length >= 1, "weekly movers are links");

// tier filter: click L3 chip → only the L3 project remains
const tierChips = q("#tierChips .chip");
assert(tierChips.length === 4, "four tier chips built");
tierChips[0].dispatchEvent(new window.Event("click", { bubbles: true }));
assert(q("#cards .pc").length === 1, "L3 tier filter narrows to 1 card");
tierChips[0].dispatchEvent(new window.Event("click", { bubbles: true }));   // off

// falling toggle → only the falling project remains, and hash records it
$("tFall").dispatchEvent(new window.Event("click", { bubbles: true }));
assert(q("#cards .pc").length === 1 &&
       q("#cards .pc")[0].textContent.indexOf("acme/faller") >= 0,
       "falling filter isolates the falling project");
assert(window.location.hash.indexOf("fall=1") >= 0, "falling state written to permalink hash");
$("tFall").dispatchEvent(new window.Event("click", { bubbles: true }));

// search + Esc
const search = $("search");
search.value = "unlicensed";
search.dispatchEvent(new window.Event("input", { bubbles: true }));
assert(q("#cards .pc").length === 1, "search narrows results");
window.document.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
assert(q("#cards .pc").length === 5, "Esc clears the search");

// density toggle flips body class
$("densBtn").dispatchEvent(new window.Event("click", { bubbles: true }));
assert(window.document.body.classList.contains("compact"), "density toggle adds compact class");

// builders view shows ORG badge + followers
window.eval("(function(){var t=document.querySelector('#tabs .tab[data-view=\"builders\"]');if(t)t.click();})()");
assert(window.document.body.textContent.indexOf("ORG") >= 0 &&
       window.document.body.textContent.indexOf("42 followers") >= 0,
       "builders board shows owner type and followers");

// donate card: hidden with empty address (default source)
assert(!$("donate").classList.contains("hidden") && $("donate").textContent.indexOf("\u0110 100") >= 0,
       "donate card visible with configured address");
assert($("donate").querySelector(".dg-inner") && $("donate").querySelector(".dg-copy"),
       "donate card has premium inner wrapper and copy button");

// donate card: visible with an address injected the way the publish script does
{
  const dom2 = new JSDOM(html, { url: "https://radar.test/", runScripts: "outside-only", pretendToBeVisual: true });
  const w2 = dom2.window;
  w2.HTMLCanvasElement.prototype.getContext = () => new Proxy({}, { get: () => noop });
  w2.fetch = window.fetch;
  w2.eval(appJs.replace(/var DONATE_DOGE='[^']*';/, "var DONATE_DOGE='';"));
  await new Promise((r) => setTimeout(r, 40));
  const d2 = w2.document.getElementById("donate");
  assert(d2.classList.contains("hidden"),
         "donate card hidden when address is emptied");
}

// AxonOS ecosystem: constellation renders and anchor card is flagged
assert(!$("ecosystem").classList.contains("hidden"), "ecosystem constellation visible");
assert($("ecosystem").textContent.indexOf("AxonOS ecosystem") >= 0, "ecosystem heading present");
assert($("ecosystem").textContent.indexOf("Singapore") >= 0, "owner location shown");
assert($("ecosystem").textContent.indexOf("denis-y") >= 0, "people/members shown");
assert($("ecosystem").textContent.indexOf("Shared maintainers") >= 0, "shared-maintainer links shown");
assert($("ecosystem").textContent.indexOf("Building across the stack") >= 0, "cross-repo people block shown");
assert($("ecosystem").querySelector(".eco-personcard"), "people rendered as structured cards");
assert($("ecosystem").querySelector(".eco-linkcard"), "links rendered as structured cards");

// Empty-signal gating: when shared lists are only org accounts (filtered to
// empty) and no cross-repo people, those blocks must be OMITTED, not shown empty.
{
  const dom3 = new JSDOM(html, { url: "https://radar.test/", runScripts: "outside-only", pretendToBeVisual: true });
  const w3 = dom3.window;
  w3.HTMLCanvasElement.prototype.getContext = () => new Proxy({}, { get: () => noop });
  const emptyEco = JSON.parse(JSON.stringify(FIXTURE));
  emptyEco.ecosystem.key_people = [];
  emptyEco.ecosystem.links = [{ a: "o/a", b: "o/b", weight: 1, shared: [] }];  // org-only → empty
  w3.fetch = (u) => String(u).includes("weekly")
    ? Promise.resolve({ ok: true, json: () => Promise.resolve(WEEKLY) })
    : Promise.resolve({ ok: true, json: () => Promise.resolve(emptyEco) });
  w3.eval(appJs);
  await new Promise((r) => setTimeout(r, 60));
  const e3 = w3.document.getElementById("ecosystem");
  assert(e3.textContent.indexOf("Building across the stack") < 0,
         "people block omitted when no cross-repo people");
  assert(e3.textContent.indexOf("Shared maintainers") < 0,
         "links block omitted when shared lists are empty");
  // but the owner constellation still shows
  assert(e3.textContent.indexOf("AxonOS ecosystem") >= 0, "ecosystem heading still present when blocks empty");
}
{
  const ecoCard = [...q("#cards .pc")].find(c => c.textContent.indexOf("axonos-kernel") >= 0);
  assert(ecoCard && ecoCard.classList.contains("eco"), "anchor repo card has .eco class");
  assert(ecoCard.textContent.indexOf("AxonOS") >= 0 && ecoCard.textContent.indexOf("Real-time neural OS kernel") >= 0,
         "anchor card shows AxonOS badge and role");
}

// zero innerHTML statically (belt & braces with the refactor)
assert(appJs.indexOf("innerHTML") < 0, "app.js contains zero innerHTML");

console.log(`\nui_smoke: ${passed} assertions passed`);
