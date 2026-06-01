// Builds the dashboard card grid + pipeline strip from window.SHIELD_MANIFEST.
// index.html sits at docs/shield root, so root prefix is "".
(function () {
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  var LINKS = [
    ["research", "Research", "research.html"],
    ["prd", "PRD", "prd.html"],
    ["trd", "TRD", "trd.html"],
    ["plan_md", "Plan", "plan.html"],
  ];
  var PIPELINE = [
    ["Research", function (a) { return a.research; }],
    ["PRD", function (a) { return a.prd; }],
    ["Plan", function (a) { return a.plan_md || a.plan_json; }],
    ["Implement", function (a, f) { return (f.reviews && f.reviews.code && f.reviews.code.count) > 0; }],
  ];
  function card(f) {
    var c = el("div", "dash-card");
    var head = el("div");
    head.appendChild(el("h3", null, f.name));
    head.appendChild(el("span", "date", f.updated ? f.updated.slice(0, 10) : ""));
    c.appendChild(head);
    var pipe = el("div", "pipeline");
    PIPELINE.forEach(function (p) {
      var done = !!p[1](f.artifacts || {}, f);
      pipe.appendChild(el("span", "pipe-step" + (done ? " done" : ""), p[0]));
    });
    c.appendChild(pipe);
    var links = el("div", "dash-links");
    LINKS.forEach(function (l) {
      if (f.artifacts && f.artifacts[l[0]]) {
        var a = el("a", null, l[1]);
        a.setAttribute("href", f.name + "/outputs/" + l[2]);
        links.appendChild(a);
      }
    });
    if (f.artifacts && f.artifacts.plan_json) {
      var aj = el("a", null, "Sidecar JSON");
      aj.setAttribute("href", f.name + "/plan.json");
      links.appendChild(aj);
    }
    c.appendChild(links);
    return c;
  }
  document.addEventListener("DOMContentLoaded", function () {
    var mount = document.getElementById("shield-dashboard");
    if (!mount) return;
    var features = (window.SHIELD_MANIFEST && window.SHIELD_MANIFEST.features) || [];
    if (!features.length) {
      mount.appendChild(el("div", "dash-empty", "No features yet — run /research or /plan to get started."));
      return;
    }
    var grid = el("div", "dash-grid");
    features.forEach(function (f) { grid.appendChild(card(f)); });
    mount.appendChild(grid);
  });
})();
