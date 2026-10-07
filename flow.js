(function (root) {
  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function step(id, title, summary, comes, happens, goes, code, tools) {
    return {
      kind: "step",
      id: id,
      title: title,
      summary: summary,
      comes: comes,
      happens: happens,
      goes: goes,
      code: code,
      tools: tools || [],
    };
  }

  var BLOCKS = [
    {
      kind: "split",
      label: "Two things enter. Neither is trusted to invent the other.",
      steps: [
        step("job", "Job description", "The role, as plain text.", "A file, or text piped into the command.", "Headings are kept for the title. The body is not sent to a model yet.", "The raw text, including any override attempt.", "cli.py brief --jd", []),
        step("locker", "Evidence locker", "Only work you can point at.", "data/profile.yaml.", "Cards have a title, a summary, skill tags, figures, and a list of what they do not prove. The editor note is not searchable.", "A list of cards.", "profile.py", []),
      ],
    },
    step("screen_job", "Screen", "This always runs, even when the tool budget is zero.", "Every line of the job.", "Lines that tell the tool to ignore the locker, pretend a job, or name an employer are removed and stored. They are not requirements.", "Kept lines, plus the removed lines shown on the brief.", "injection.py, jd.py", ["screen_job"]),
    step("parse_requirements", "Read the ask", "Only known skills and a digit number of years become requirements.", "The kept lines.", "A longer line wins when the same skill appears twice, because it usually names the skill more clearly. A sentence the lexicon does not know is listed as unmapped, not guessed.", "Requirements, each with a skill and a kind: skill, or years.", "jd.py, skills.py", ["parse_requirements"]),
    step("search_evidence", "Search cards", "A card must already list the skill.", "One requirement.", "Cards without that skill are invisible. BM25 only orders the cards that have it. A tie breaks on the card id, so the same job always picks the same card.", "Up to three cards, or none.", "index.py search_cards", ["search_evidence"]),
    step("read_card", "Read the card", "No claim is written from a search hit alone.", "The top card id.", "The summary, figures, and limits are loaded. If the budget runs out before this read, the requirement stays unreviewed.", "The full card, or a stop.", "agent.py read_card", ["read_card"]),
    step("commit_claim", "Write the sentence", "The sentence is a template.", "The requirement and the card, or the news that there is no card.", "A supported sentence is the title, the summary, and the recorded figures. A years request is never supported: the sentence says how many cards list the skill and that the duration is not claimed.", "One claim: supported, gap, or unreviewed.", "wording.py, agent.py", ["commit_claim"]),
    {
      kind: "split",
      label: "What that sentence is allowed to be.",
      steps: [
        step("supported", "Covered", "The card lists the skill.", "A skill requirement and a card.", "The brief groups these under the project and repeats what the card does not prove.", "A cited project.", "brief.py Covered", ["commit_claim"]),
        step("gap", "Not claimed", "No card, or a duration.", "A miss, or a years line.", "The gap stays in the brief. It is the study list, not a line for a CV.", "An explicit gap.", "brief.py Not claimed", ["commit_claim"]),
        step("unreviewed", "Not reviewed", "The lookup budget ran out.", "Requirements still waiting.", "They are not claimed and not called gaps. The screen and the verifier still ran.", "An unreviewed line.", "agent.py budget", []),
      ],
    },
    step("verify_claims", "Verifier", "This also always runs.", "Every supported sentence.", "Faithfulness means the sentence is exactly the template and the card lists the skill. Number fidelity means every digit in that sentence appears on the card. A years line marked supported fails on purpose.", "1.00 and 1.00, or a brief you must not send.", "verify.py", ["verify_claims"]),
    step("brief", "Brief and trace", "The page and the markdown read this.", "The claims, the removed lines, and the unmapped lines.", "Markdown goes to the terminal. JSON goes to the dashboard. The trace lists safety steps and counted lookups separately.", "runs/brief.md and runs/brief.json.", "brief.py", []),
    {
      kind: "split",
      label: "Optional after the brief exists. Neither one can invent a claim.",
      steps: [
        step("prose", "Model echo", "Off unless you pass --live.", "The finished sentences only. Not the blocked lines.", "grok-4.7 is asked to copy them with a Covered or Gap prefix. One changed word and the draft is dropped.", "The same sentences, or nothing.", "prose.py", ["prose"]),
        step("gate", "Release gate", "Five saved jobs, on every push.", "The golden file and the thresholds.", "Support, gaps, injection refusal, faithfulness, and number fidelity all have to be 1.00.", "CI passes, or the build fails.", "evals.py, .github/workflows/ci.yml", []),
        step("mcp", "MCP tools", "A client can ask for a brief. It cannot write one.", "list, search, screen, or build.", "build_brief calls the same loop. There is no tool whose argument is a claim sentence.", "Template text, or an error if the verifier fails.", "mcp_server.py", []),
      ],
    },
  ];

  function findStep(id) {
    var found = null;
    BLOCKS.forEach(function (block) {
      if (found) return;
      if (block.kind === "step" && block.id === id) found = block;
      if (block.kind === "split") {
        block.steps.forEach(function (item) { if (item.id === id) found = item; });
      }
    });
    return found;
  }

  function ran(item, tools, run) {
    if (item.id === "supported") return run && (run.covered || []).length > 0;
    if (item.id === "gap") return run && (run.gaps || []).some(function (row) { return row.status !== "unreviewed"; });
    if (item.id === "unreviewed") return run && (run.gaps || []).some(function (row) { return row.status === "unreviewed"; });
    if (item.id === "brief") return !!run;
    if (item.id === "job" || item.id === "locker") return !!run;
    if (!item.tools.length) return false;
    return item.tools.some(function (name) { return tools[name]; });
  }

  function button(item, selected, tools, run) {
    var classes = "station";
    if (item.id === selected) classes += " on";
    if (ran(item, tools, run)) classes += " ran";
    return '<button type="button" class="' + classes + '" data-flow-step="' + esc(item.id) + '"><b>' +
      esc(item.title) + "</b><small>" + esc(item.summary) + "</small></button>";
  }

  function render(run, selectedId) {
    var tools = {};
    var trace = (run && run.trace) || [];
    trace.forEach(function (event) { tools[event.tool] = true; });
    var selected = findStep(selectedId) || findStep("screen_job");
    var body = BLOCKS.map(function (block) {
      if (block.kind === "step") return "<li>" + button(block, selected.id, tools, run) + "</li>";
      return '<li class="flow-split"><p>' + esc(block.label) + '</p><div class="flow-choices">' +
        block.steps.map(function (item) { return button(item, selected.id, tools, run); }).join("") +
        "</div></li>";
    }).join("");
    var events = trace.filter(function (event) { return selected.tools.indexOf(event.tool) !== -1; });
    var runHtml;
    if (selected.id === "supported" && run) {
      runHtml = "<h3>This run</h3><p>" + (run.covered || []).length + " requirements were covered.</p>";
    } else if (selected.id === "gap" && run) {
      var gaps = (run.gaps || []).filter(function (row) { return row.status !== "unreviewed"; });
      runHtml = "<h3>This run</h3><ul>" + gaps.map(function (row) {
        return "<li>" + esc(row.skill_label) + "</li>";
      }).join("") + "</ul>";
    } else if (events.length) {
      runHtml = "<h3>This run</h3><ul>" + events.map(function (event) {
        return "<li>" + esc(event.detail) + "</li>";
      }).join("") + "</ul>";
    } else if (run) {
      runHtml = '<p class="flow-quiet">Nothing in the loaded brief stopped on this step.</p>';
    } else {
      runHtml = '<p class="flow-quiet">Open a brief JSON and the steps that ran will be marked.</p>';
    }
    var banner = run
      ? '<p class="flow-banner">' + esc(run.job_title || "Loaded brief") + " · lookups " +
        esc(run.tool_calls) + " of " + esc(run.budget) + " · faithfulness " +
        esc(run.checks && run.checks.faithfulness) + "</p>"
      : "";
    return '<section class="flow"><p class="meta">Follow one job through the loop</p><h2>What comes in, where it goes</h2>' +
      '<p class="lede">Marked steps are the ones in the brief that is loaded. Select a step to see what enters it and what leaves.</p>' +
      banner +
      '<div class="flow-layout"><ol class="flow-list">' + body + "</ol>" +
      '<article class="flow-detail"><p class="meta">Selected step</p><h3>' + esc(selected.title) + "</h3><dl>" +
      "<dt>Comes in</dt><dd>" + esc(selected.comes) + "</dd>" +
      "<dt>What happens</dt><dd>" + esc(selected.happens) + "</dd>" +
      "<dt>Goes out</dt><dd>" + esc(selected.goes) + "</dd>" +
      "<dt>In the code</dt><dd>" + esc(selected.code) + "</dd></dl>" +
      runHtml + "</article></div></section>";
  }

  root.ClaimlineFlow = { render: render };
})(typeof window !== "undefined" ? window : globalThis);
