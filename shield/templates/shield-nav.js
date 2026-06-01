// Builds the nested Docs ▾ dropdown from window.SHIELD_MANIFEST.
// Link paths are prefixed with document.body.dataset.shieldRoot so they
// resolve from any page depth. No fetch — data comes from manifest.js.
(function () {
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  var ARTIFACTS = [
    ["research", "Research", "research.html"],
    ["prd", "PRD", "prd.html"],
    ["trd", "TRD", "trd.html"],
    ["plan_md", "Plan", "plan.html"],
    ["plan_arch_md", "Architecture", "plan-architecture.html"],
  ];
  function buildDocsMenu(manifest, root) {
    var frag = document.createDocumentFragment();
    var features = (manifest && manifest.features) || [];
    if (!features.length) {
      frag.appendChild(el("div", "docs-group", "No docs yet"));
      return frag;
    }
    features.forEach(function (f) {
      var det = el("details", "docs-feature");
      det.appendChild(el("summary", null, f.name));
      ARTIFACTS.forEach(function (a) {
        if (f.artifacts && f.artifacts[a[0]]) {
          var href = root + f.name + "/outputs/" + a[2];
          var link = el("a", "docs-link", a[1]);
          link.setAttribute("href", href);
          det.appendChild(link);
        }
      });
      ["prd", "plan", "code"].forEach(function (rt) {
        var rv = f.reviews && f.reviews[rt];
        if (rv && rv.entries && rv.entries.length) {
          det.appendChild(el("div", "docs-group", rt + " reviews"));
          rv.entries.forEach(function (en) {
            var link = el("a", "docs-link", en.date);
            link.setAttribute("href", root + en.path);
            det.appendChild(link);
          });
        }
      });
      frag.appendChild(det);
    });
    return frag;
  }
  document.addEventListener("DOMContentLoaded", function () {
    var root = document.body.dataset.shieldRoot || "";
    var dropdown = document.getElementById("docs-dropdown");
    var toggle = document.getElementById("docs-toggle");
    if (dropdown) dropdown.appendChild(buildDocsMenu(window.SHIELD_MANIFEST, root));
    if (toggle && dropdown) {
      toggle.addEventListener("click", function () {
        var open = dropdown.classList.toggle("open");
        toggle.setAttribute("aria-expanded", String(open));
      });
      document.addEventListener("click", function (e) {
        if (!e.target.closest(".docs-menu")) dropdown.classList.remove("open");
      });
    }
  });
})();
