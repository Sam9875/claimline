(function (root) {
  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  var BOXES = [
    { id: "job", title: "Job description", line: "The role, as text.", detail: "A file, or text passed to claimline brief. The text is not trusted. A line in it may try to make the tool invent an employer, a team, or a title." },
    { id: "locker", title: "Evidence locker", line: "Cards for public repositories.", detail: "data/profile.yaml. Each card has a title, a summary, skill tags, figures, and a list of what it does not prove. The locker is not a resume." },
    { id: "screen", title: "Screen", line: "This always runs.", detail: "Lines that say to ignore the locker, pretend a job, or name an employer are removed. They are shown on the brief and they are not requirements. This still runs when the lookup budget is zero." },
    { id: "parse", title: "Read the ask", line: "Known skills, and years.", detail: "Only skills the lexicon already knows become requirements. A line it does not know is listed as unmapped. It is not guessed. A number of years becomes its own requirement." },
    { id: "search", title: "Search cards", line: "The skill must already be listed.", detail: "Cards without that skill are invisible. Word overlap only orders the cards that have it. A tie breaks on the card id, so the same job picks the same card." },
    { id: "read", title: "Read the card", line: "A search hit is not a claim.", detail: "The summary, the figures, and the limits are loaded. If the budget runs out before this read, the requirement stays not reviewed." },
    { id: "write", title: "Write the sentence", line: "A template, not a free draft.", detail: "A covered sentence is the card title, the summary, and the recorded figures. A request for years is never covered. The sentence says the duration is not claimed." },
    { id: "covered", title: "Covered", line: "The card lists the skill.", detail: "The brief groups these under the project and repeats what the card does not prove." },
    { id: "gap", title: "Gap", line: "Not claimed.", detail: "No card has the skill, or the line asked for years. A gap is a study item. It is not a line for a CV." },
    { id: "unreviewed", title: "Not reviewed", line: "The budget ran out.", detail: "These lines are not covered, and they are not called gaps. The screen and the verifier still ran." },
    { id: "verify", title: "Verifier", line: "This always runs.", detail: "A covered sentence must be exactly the template, and the card must list the skill. Every digit in that sentence must already be on the card. A years line marked covered fails this check." },
    { id: "brief", title: "Brief", line: "What you can read.", detail: "Markdown goes to the terminal. JSON can be opened on this page. The website shows one sample brief. It does not run a new job, and it does not upload the file." },
    { id: "prose", title: "Model echo", line: "Optional. One changed word is rejected.", detail: "Off unless you pass --live. grok-4.7 is asked to copy the finished sentences. If any word changes, the draft is dropped and the template sentences stay." },
    { id: "gate", title: "Release gate", line: "The build fails if a claim is loose.", detail: "On every push, support, gaps, injection refusal, faithfulness, and number fidelity all have to be 1.00." },
    { id: "mcp", title: "MCP tools", line: "A client can ask. It cannot write a claim.", detail: "The tools are list, search, screen, and build. Build uses the same loop. There is no tool whose argument is a claim sentence." },
  ];

  function byId(id) {
    for (var i = 0; i < BOXES.length; i++) if (BOXES[i].id === id) return BOXES[i];
    return null;
  }

  function box(id, selected) {
    var item = byId(id);
    var on = id === selected ? " on" : "";
    return '<button type="button" class="arch-box' + on + '" data-arch="' + esc(id) + '"><b>' +
      esc(item.title) + "</b><small>" + esc(item.line) + "</small></button>";
  }

  function arrow() {
    return '<span class="arch-to" aria-hidden="true"></span>';
  }

  function fan(ids, selected) {
    return '<div class="arch-fan">' + ids.map(function (id) { return box(id, selected); }).join("") + "</div>";
  }

  function chain(ids, selected) {
    return ids.map(function (id) { return box(id, selected); }).join(arrow());
  }

  function lane(label, inner) {
    return '<section class="arch-lane"><p class="arch-label">' + esc(label) + '</p><div class="arch-flow">' + inner + "</div></section>";
  }

  function down() {
    return '<div class="arch-down" aria-hidden="true"></div>';
  }

  function render(selectedId) {
    var selected = byId(selectedId) || byId("screen");
    var board = [
      lane("What comes in", fan(["job", "locker"], selected.id) + arrow() + box("screen", selected.id)),
      lane("Every job, in this order", chain(["parse", "search", "read", "write"], selected.id)),
      lane("What that sentence is allowed to be", fan(["covered", "gap", "unreviewed"], selected.id)),
      lane("The check, then the page", chain(["verify", "brief"], selected.id)),
      lane("Optional. None of these can invent a claim.", fan(["prose", "gate", "mcp"], selected.id)),
    ].join(down());
    return '<div class="arch"><h2>The pieces.</h2>' +
      '<p class="lede">Follow the arrows from top to bottom. Click a box to read what happens there. How it moves marks these steps for the brief that is loaded.</p>' +
      '<div class="arch-board" role="group" aria-label="Architecture of the evidence brief">' + board + "</div>" +
      '<article class="arch-note" id="arch-note"><h2>' + esc(selected.title) + "</h2><p>" + esc(selected.detail) + "</p></article></div>";
  }

  root.ClaimlineMap = { render: render };
})(typeof globalThis !== "undefined" ? globalThis : this);
