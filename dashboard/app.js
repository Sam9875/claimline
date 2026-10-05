(function (root) {
  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function renderClaimline(run) {
    var checks = run.checks || {};
    var covered = run.covered || [];
    var gaps = run.gaps || [];
    var faith = Number(checks.faithfulness);
    var numbers = Number(checks.number_fidelity);
    var faithText = Number.isFinite(faith) ? faith.toFixed(2) : "n/a";
    var numberText = Number.isFinite(numbers) ? numbers.toFixed(2) : "n/a";
    var cards = {};
    covered.forEach(function (row) {
      var key = row.card_id || row.card_title;
      if (!cards[key]) cards[key] = [];
      cards[key].push(row);
    });
    var coveredHtml = Object.keys(cards).map(function (key) {
      var rows = cards[key];
      var first = rows[0];
      var limits = (first.limits || []).map(function (limit) {
        return "<li>" + esc(limit) + "</li>";
      }).join("");
      var claims = rows.map(function (row) {
        return "<li><span class=\"tag\">" + esc(row.skill_label) + "</span> " + esc(row.statement) + "</li>";
      }).join("");
      var link = first.url ? "<p><a href=\"" + esc(first.url) + "\">" + esc(first.url) + "</a></p>" : "";
      var limitBlock = limits ? "<p class=\"meta\">This project does not prove:</p><ul>" + limits + "</ul>" : "";
      return "<article class=\"covered\"><h3>" + esc(first.card_title) + "</h3>" + link + "<ul>" + claims + "</ul>" + limitBlock + "</article>";
    }).join("");
    if (!coveredHtml) {
      coveredHtml = "<article class=\"covered\"><p>No requirement was covered.</p></article>";
    }
    var gapHtml = gaps.map(function (row) {
      var label = row.kind === "experience_years" ? "Years requested" : row.skill_label;
      return "<article class=\"gap\"><h3>" + esc(label) + "</h3><p>" + esc(row.statement) + "</p></article>";
    }).join("");
    if (!gapHtml) {
      gapHtml = "<article class=\"gap\"><p>No gaps in the parsed requirements.</p></article>";
    }
    var unmapped = (run.unmapped || []).map(function (line) {
      return "<li>" + esc(line) + "</li>";
    }).join("");
    var blocked = (run.blocked || []).map(function (line) {
      return "<li>" + esc(line) + "</li>";
    }).join("");
    var trace = (run.trace || []).map(function (event) {
      var kind = event.counted ? "counted" : "safety";
      return "<li><code>" + esc(event.tool) + "</code> (" + kind + ") " + esc(event.detail) + "</li>";
    }).join("");
    return [
      "<header>",
      "<p class=\"meta\">" + esc(run.candidate || "Candidate") + "</p>",
      "<h1>" + esc(run.job_title || "Job brief") + "</h1>",
      "<p class=\"lede\">Projects that match the role are listed with the limit of what they prove. A gap stays a gap.</p>",
      "</header>",
      "<section class=\"stats\">",
      "<div class=\"stat\"><b>" + covered.length + "</b><span>Requirements covered</span></div>",
      "<div class=\"stat\"><b>" + gaps.length + "</b><span>Still a gap</span></div>",
      "<div class=\"stat\"><b>" + faithText + "</b><span>Faithfulness, numbers " + numberText + "</span></div>",
      "</section>",
      "<div class=\"layout\">",
      "<section><h2>Projects that cover the ask</h2>" + coveredHtml + "</section>",
      "<section><h2>Still a gap</h2>" + gapHtml + "</section>",
      "</div>",
      unmapped ? "<section class=\"notice\"><h2>Lines to read yourself</h2><ul>" + unmapped + "</ul></section>" : "",
      blocked ? "<section class=\"notice\"><h2>Instructions that were thrown out</h2><ul>" + blocked + "</ul></section>" : "",
      "<section class=\"trace\"><h2>Steps the loop took</h2><ol>" + trace + "</ol></section>"
    ].join("");
  }

  root.renderClaimline = renderClaimline;

  function mount(run) {
    var app = document.getElementById("app");
    if (!app) return;
    app.innerHTML = renderClaimline(run);
  }

  if (typeof document !== "undefined" && document && document.getElementById) {
    document.addEventListener("DOMContentLoaded", function () {
      if (root.CLAIMLINE_SAMPLE) mount(root.CLAIMLINE_SAMPLE);
      var input = document.getElementById("run-file");
      if (!input) return;
      input.addEventListener("change", function () {
        var file = input.files && input.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function () {
          mount(JSON.parse(String(reader.result)));
        };
        reader.readAsText(file);
      });
    });
  }
})(typeof window !== "undefined" ? window : globalThis);
