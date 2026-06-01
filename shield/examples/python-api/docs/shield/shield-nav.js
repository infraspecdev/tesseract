// Builds the header breadcrumb + the filterable Features panel from
// window.SHIELD_MANIFEST. Breadcrumb is derived from the URL path +
// data-shield-root. No fetch — data comes from manifest.js. file:// safe.
(function () {
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  // artifact key -> [label, filename, tag]
  var ARTIFACTS = [
    ["research", "Research", "research.html", "research"],
    ["prd", "PRD", "prd.html", "prd"],
    ["trd", "TRD", "trd.html", "trd"],
    ["plan_md", "Plan", "plan.html", "plan"],
    ["plan_arch_md", "Architecture", "plan-architecture.html", "arch"],
    ["plan_json", "Sidecar JSON", "../plan.json", "json"],
  ];
  // filename -> breadcrumb label for the active doc
  var FILE_LABELS = {
    "prd.html": "PRD", "trd.html": "TRD", "plan.html": "Plan",
    "research.html": "Research", "plan-architecture.html": "Architecture",
    "summary.html": "Review", "enhanced-prd.html": "Enhanced PRD",
    "enhanced-plan.html": "Enhanced Plan", "index.html": "Dashboard",
  };

  function titleize(file) {
    return file.replace(/\.html$/, "").replace(/[-_]/g, " ")
      .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }

  // ---- Breadcrumb (from path) ----
  function buildCrumb(root) {
    var crumb = document.getElementById("shield-crumb");
    if (!crumb) return;
    var parts = decodeURIComponent(location.pathname).split("/").filter(Boolean);
    var file = parts[parts.length - 1] || "index.html";
    var dash = el("a", null, "Dashboard");
    dash.setAttribute("href", root + "index.html");
    crumb.appendChild(dash);

    var oi = parts.lastIndexOf("outputs");
    if (file === "index.html" || oi <= 0) {
      // dashboard (or unknown) — just mark Dashboard active
      dash.className = "here";
      dash.removeAttribute("href");
      return;
    }
    var feature = parts[oi - 1];
    crumb.appendChild(el("span", "chev", "›"));
    crumb.appendChild(el("span", null, feature));

    var ri = parts.lastIndexOf("reviews");
    crumb.appendChild(el("span", "chev", "›"));
    if (ri !== -1 && ri > oi) {
      var rtype = parts[ri + 1] || "", rdate = parts[ri + 2] || "";
      crumb.appendChild(el("span", "here", rtype + " review · " + rdate));
    } else {
      crumb.appendChild(el("span", "here", FILE_LABELS[file] || titleize(file)));
    }
  }

  // ---- Features panel (grouped, filterable) ----
  function matches(q, s) { return s.toLowerCase().indexOf(q) !== -1; }

  function buildResults(manifest, root, q) {
    var frag = document.createDocumentFragment();
    var features = (manifest && manifest.features) || [];
    var query = (q || "").trim().toLowerCase();
    var shown = 0;
    features.forEach(function (f) {
      var featMatch = matches(query, f.name);
      var docs = [];
      ARTIFACTS.forEach(function (a) {
        if (f.artifacts && f.artifacts[a[0]]) {
          if (!query || featMatch || matches(query, a[1])) docs.push(a);
        }
      });
      var revs = [];
      ["prd", "plan", "code"].forEach(function (rt) {
        var rv = f.reviews && f.reviews[rt];
        if (rv && rv.entries) {
          rv.entries.forEach(function (en) {
            var label = rt + " review · " + en.date;
            if (!query || featMatch || matches(query, label))
              revs.push({ label: label, path: en.path });
          });
        }
      });
      if (!docs.length && !revs.length) return;
      shown++;
      frag.appendChild(el("div", "feat-name", f.name));
      docs.forEach(function (a) {
        var href = a[2].indexOf("../") === 0
          ? root + f.name + "/" + a[2].slice(3)
          : root + f.name + "/outputs/" + a[2];
        var link = el("a", "doc", a[1] + '<span class="tag">' + a[3] + "</span>");
        link.setAttribute("href", href);
        frag.appendChild(link);
      });
      revs.forEach(function (r) {
        var link = el("a", "doc rev", "↳ " + r.label);
        link.setAttribute("href", root + r.path);
        frag.appendChild(link);
      });
    });
    if (!shown) frag.appendChild(el("div", "docs-empty", 'No docs match "' + query + '"'));
    return frag;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var root = document.body.dataset.shieldRoot || "";
    buildCrumb(root);

    var btn = document.getElementById("docs-toggle");
    var panel = document.getElementById("docs-panel");
    var search = document.getElementById("docs-search");
    var results = document.getElementById("docs-results");
    if (!btn || !panel || !search || !results) return;

    function paint() {
      results.innerHTML = "";
      results.appendChild(buildResults(window.SHIELD_MANIFEST, root, search.value));
    }
    function open() {
      panel.classList.add("open"); btn.setAttribute("aria-expanded", "true");
      search.value = ""; paint(); search.focus();
    }
    function close() {
      panel.classList.remove("open"); btn.setAttribute("aria-expanded", "false");
    }
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
