const assert = require("assert");
require("../dashboard/map.js");

const map = globalThis.ClaimlineMap;
assert.ok(map && map.render);

const html = map.render("screen");
assert.ok(html.includes('class="arch-board"'));
assert.ok(html.includes('class="arch-to"'));
assert.ok(html.includes('class="arch-down"'));
["Job description", "Evidence locker", "Screen", "Read the ask", "Search cards", "Read the card", "Write the sentence", "Covered", "Gap", "Not reviewed", "Verifier", "Brief", "Model echo", "Release gate", "MCP tools"].forEach(function (title) {
  assert.ok(html.includes(title), "missing " + title);
});
assert.ok(html.includes("lookup budget is zero"));
assert.ok(html.includes("arch-box on"));

const years = map.render("write");
assert.ok(years.includes("never covered"));
assert.ok(!years.includes("lookup budget is zero"));

const hostile = map.render("<img>");
assert.ok(!hostile.includes("<img>"));
assert.ok(hostile.includes("lookup budget is zero"));
