// Unit tests for shield-nav.js pure logic. Run: node --test shield/templates/
// Zero deps — uses Node's built-in test runner. The DOM bootstrap in
// shield-nav.js is guarded by `typeof document`, so requiring it here is safe.
const test = require("node:test");
const assert = require("node:assert/strict");
const { crumbModel, filterFeatures, titleize } = require("./shield-nav.js");

// ---------- crumbModel ----------

test("crumbModel: dashboard (index.html) is the active root", () => {
  assert.deepEqual(crumbModel("/docs/shield/index.html", ""), [
    { label: "Dashboard", href: null, active: true },
  ]);
});

test("crumbModel: doc page → Dashboard › feature › docType", () => {
  const m = crumbModel("/x/docs/shield/backlog-20260527/outputs/prd.html", "../../");
  assert.equal(m.length, 3);
  assert.deepEqual(m[0], { label: "Dashboard", href: "../../index.html", active: false });
  assert.deepEqual(m[1], { label: "backlog-20260527", href: null, active: false });
  assert.deepEqual(m[2], { label: "PRD", href: null, active: true });
});

test("crumbModel: review page → '<type> review · <date>'", () => {
  const m = crumbModel(
    "/docs/shield/backlog-20260527/outputs/reviews/plan/2026-05-25/summary.html",
    "../../../../",
  );
  assert.equal(m[1].label, "backlog-20260527");
  assert.deepEqual(m[m.length - 1], {
    label: "plan review · 2026-05-25", href: null, active: true,
  });
});

test("crumbModel: unknown filename is titleized", () => {
  const m = crumbModel("/docs/shield/feat-a/outputs/some-doc.html", "../../");
  assert.equal(m[2].label, "Some Doc");
});

test("titleize: strips .html and title-cases kebab/snake", () => {
  assert.equal(titleize("enhanced_plan.html"), "Enhanced Plan");
  assert.equal(titleize("foo-bar-baz.html"), "Foo Bar Baz");
});

// ---------- filterFeatures ----------

const MANIFEST = {
  features: [
    {
      name: "backlog",
      artifacts: { prd: true, trd: true, plan_md: true, plan_json: true },
      reviews: {
        prd: { entries: [{ date: "2026-05-27", path: "backlog/outputs/reviews/prd/2026-05-27/summary.html" }] },
        plan: { entries: [{ date: "2026-05-29", path: "backlog/outputs/reviews/plan/2026-05-29/summary.html" }] },
      },
    },
    { name: "research-only", artifacts: { research: true }, reviews: {} },
  ],
};

test("filterFeatures: no query returns all features with their docs", () => {
  const r = filterFeatures(MANIFEST, "", "");
  assert.equal(r.length, 2);
  assert.equal(r[0].name, "backlog");
  assert.deepEqual(r[0].docs.map((d) => d.label), ["PRD", "TRD", "Plan", "Sidecar JSON"]);
});

test("filterFeatures: plan_json href resolves to <feature>/plan.json (regression guard)", () => {
  const r = filterFeatures(MANIFEST, "", "../../");
  assert.equal(r[0].docs.find((d) => d.tag === "json").href, "../../backlog/plan.json");
  assert.equal(r[0].docs.find((d) => d.tag === "prd").href, "../../backlog/outputs/prd.html");
});

test("filterFeatures: query 'plan' keeps only plan docs + plan reviews", () => {
  const r = filterFeatures(MANIFEST, "plan", "");
  assert.equal(r.length, 1); // research-only drops out
  assert.ok(r[0].docs.every((d) => /plan/i.test(d.label)));
  assert.ok(r[0].reviews.every((rv) => /plan/i.test(rv.label)));
  assert.equal(r[0].reviews.length, 1);
});

test("filterFeatures: feature-name match includes all that feature's docs", () => {
  const r = filterFeatures(MANIFEST, "research-only", "");
  assert.equal(r.length, 1);
  assert.deepEqual(r[0].docs.map((d) => d.label), ["Research"]);
});

test("filterFeatures: no match → empty array", () => {
  assert.deepEqual(filterFeatures(MANIFEST, "zzz", ""), []);
});

test("filterFeatures: review entry → label + path-based href", () => {
  const r = filterFeatures(MANIFEST, "", "../../");
  const rev = r[0].reviews.find((x) => /plan review/.test(x.label));
  assert.equal(rev.label, "plan review · 2026-05-29");
  assert.equal(rev.href, "../../backlog/outputs/reviews/plan/2026-05-29/summary.html");
});

test("filterFeatures: tolerates missing manifest", () => {
  assert.deepEqual(filterFeatures(null, "", ""), []);
  assert.deepEqual(filterFeatures({}, "", ""), []);
});
