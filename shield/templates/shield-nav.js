// Header breadcrumb + filterable Features panel, built from window.SHIELD_MANIFEST.
// Pure logic (crumbModel, filterFeatures, titleize) is separated from DOM
// rendering and exported for unit tests (node:test). The DOM bootstrap is
// guarded by `typeof document`, so requiring this file in Node is safe.
// No fetch — data comes from manifest.js. file:// safe.
(function () {
  var FILE_LABELS = {
    "prd.html": "PRD", "trd.html": "TRD", "plan.html": "Plan",
    "research.html": "Research", "plan-architecture.html": "Architecture",
    "summary.html": "Review", "enhanced-prd.html": "Enhanced PRD",
    "enhanced-plan.html": "Enhanced Plan", "index.html": "Dashboard",
  };
  // artifact key -> [label, path-within-feature, tag]
  var ARTIFACTS = [
    ["research", "Research", "outputs/research.html", "research"],
    ["prd", "PRD", "outputs/prd.html", "prd"],
    ["trd", "TRD", "outputs/trd.html", "trd"],
    ["plan_md", "Plan", "outputs/plan.html", "plan"],
    ["plan_arch_md", "Architecture", "outputs/plan-architecture.html", "arch"],
    ["plan_json", "Sidecar JSON", "plan.json", "json"],
  ];

  function titleize(file) {
    return file.replace(/\.html$/, "").replace(/[-_]/g, " ")
      .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  // Breadcrumb model from a URL path + the page's root prefix.
  // Returns [{label, href|null, active}].
  function crumbModel(pathname, root) {
    var parts = decodeURIComponent(pathname).split("/").filter(Boolean);
    var file = parts[parts.length - 1] || "index.html";
    var oi = parts.lastIndexOf("outputs");
    if (file === "index.html" || oi <= 0) {
      return [{ label: "Dashboard", href: null, active: true }];
    }
    var crumb = [{ label: "Dashboard", href: root + "index.html", active: false }];
    crumb.push({ label: parts[oi - 1], href: null, active: false });
    var ri = parts.lastIndexOf("reviews");
    if (ri !== -1 && ri > oi) {
      crumb.push({ label: (parts[ri + 1] || "") + " review · " + (parts[ri + 2] || ""), href: null, active: true });
    } else {
      crumb.push({ label: FILE_LABELS[file] || titleize(file), href: null, active: true });
    }
    return crumb;
  }

  // Filtered, grouped feature model from the manifest + a search query.
  // Returns [{name, docs:[{label,href,tag}], reviews:[{label,href}]}].
  function filterFeatures(manifest, query, root) {
    var features = (manifest && manifest.features) || [];
    var q = (query || "").trim().toLowerCase();
    var out = [];
    features.forEach(function (f) {
      var fm = f.name.toLowerCase().indexOf(q) !== -1;
      var docs = [];
      ARTIFACTS.forEach(function (a) {
        if (f.artifacts && f.artifacts[a[0]] && (!q || fm || a[1].toLowerCase().indexOf(q) !== -1)) {
          docs.push({ label: a[1], href: root + f.name + "/" + a[2], tag: a[3] });
        }
      });
      var reviews = [];
      ["prd", "plan", "code"].forEach(function (rt) {
        var rv = f.reviews && f.reviews[rt];
        if (rv && rv.entries) {
          rv.entries.forEach(function (en) {
            var label = rt + " review · " + en.date;
            if (!q || fm || label.toLowerCase().indexOf(q) !== -1) {
              reviews.push({ label: label, href: root + en.path });
            }
          });
        }
      });
      if (docs.length || reviews.length) out.push({ name: f.name, docs: docs, reviews: reviews });
    });
    return out;
  }

  // Export pure logic for unit tests (Node). Browsers load this as a classic
  // script where `module` is undefined, so this branch is a no-op there.
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { crumbModel: crumbModel, filterFeatures: filterFeatures, titleize: titleize };
  }

  // Below here is browser-only DOM wiring.
  if (typeof document === "undefined") return;

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  function renderCrumb(model) {
    var crumb = document.getElementById("shield-crumb");
    if (!crumb) return;
    crumb.innerHTML = "";
    model.forEach(function (seg, i) {
      if (i) crumb.appendChild(el("span", "chev", "›"));
      if (seg.href) {
        var a = el("a", seg.active ? "here" : null, seg.label);
        a.setAttribute("href", seg.href);
        crumb.appendChild(a);
      } else {
        crumb.appendChild(el("span", seg.active ? "here" : null, seg.label));
      }
    });
  }

  function renderResults(model, container) {
    container.innerHTML = "";
    if (!model.length) { container.appendChild(el("div", "docs-empty", "No docs match")); return; }
    model.forEach(function (f) {
      container.appendChild(el("div", "feat-name", f.name));
      f.docs.forEach(function (d) {
        var a = el("a", "doc", d.label + '<span class="tag">' + d.tag + "</span>");
        a.setAttribute("href", d.href);
        container.appendChild(a);
      });
      f.reviews.forEach(function (r) {
        var a = el("a", "doc rev", "↳ " + r.label);
        a.setAttribute("href", r.href);
        container.appendChild(a);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var root = document.body.dataset.shieldRoot || "";
    renderCrumb(crumbModel(location.pathname, root));

    var btn = document.getElementById("docs-toggle");
    var panel = document.getElementById("docs-panel");
    var search = document.getElementById("docs-search");
    var results = document.getElementById("docs-results");
    if (!btn || !panel || !search || !results) return;

    function paint() { renderResults(filterFeatures(window.SHIELD_MANIFEST, search.value, root), results); }
    function open() {
      panel.classList.add("open"); btn.setAttribute("aria-expanded", "true");
      search.value = ""; paint(); search.focus();
    }
    function close() { panel.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); }

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      panel.classList.contains("open") ? close() : open();
    });
    search.addEventListener("input", paint);
    search.addEventListener("click", function (e) { e.stopPropagation(); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); open(); }
    });
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".feat-wrap")) close();
    });
  });
})();
