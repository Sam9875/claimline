const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

function stationClass(html, id) {
  const needle = 'data-flow-step="' + id + '"';
  const at = html.indexOf(needle);
  assert.ok(at !== -1, "missing step " + id);
  const start = html.lastIndexOf("<button", at);
  const tag = html.slice(start, at);
  const match = tag.match(/class="([^"]*)"/);
  return match ? match[1] : "";
}

const listeners = {};
const elements = {};
function makeEl(id) {
  const el = {
    id: id,
    innerHTML: "",
    files: null,
    classList: { toggle: function () {} },
    addEventListener: function (name, fn) { el["on" + name] = fn; },
  };
  elements[id] = el;
  return el;
}
["app", "tab-brief", "tab-flow", "run-file"].forEach(makeEl);

const document = {
  getElementById: function (id) { return elements[id] || null; },
  addEventListener: function (name, fn) { listeners[name] = fn; },
};
const context = { window: {}, document: document, console: console, FileReader: function () {} };
context.window = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync("dashboard/sample-run.js", "utf8"), context);
vm.runInContext(fs.readFileSync("dashboard/flow.js", "utf8"), context);
vm.runInContext(fs.readFileSync("dashboard/app.js", "utf8"), context);

listeners.DOMContentLoaded();
const opened = elements.app.innerHTML;
assert.ok(opened.includes("Comes in"));
assert.ok(opened.includes("What happens"));
assert.ok(opened.includes("Goes out"));
assert.ok(stationClass(opened, "screen_job").includes("ran"));
assert.ok(stationClass(opened, "search_evidence").includes("ran"));
assert.ok(stationClass(opened, "verify_claims").includes("ran"));
assert.ok(stationClass(opened, "supported").includes("ran"));
assert.ok(stationClass(opened, "gap").includes("ran"));
assert.ok(!stationClass(opened, "unreviewed").includes("ran"));
assert.ok(!stationClass(opened, "prose").includes("ran"));

function click(attrs) {
  listeners.click({
    target: {
      closest: function (sel) {
        if (sel === "[data-tab]" && attrs["data-tab"]) {
          return { getAttribute: function (key) { return attrs[key]; } };
        }
        if (sel === "[data-flow-step]" && attrs["data-flow-step"]) {
          return { getAttribute: function (key) { return attrs[key]; } };
        }
        return null;
      },
    },
  });
}

click({ "data-flow-step": "supported" });
assert.ok(elements.app.innerHTML.includes("requirements were covered"));
click({ "data-flow-step": "gap" });
assert.ok(elements.app.innerHTML.includes("Docker"));
assert.ok(elements.app.innerHTML.includes("Kubernetes"));
click({ "data-tab": "brief" });
assert.ok(elements.app.innerHTML.includes("Projects that cover the ask"));
assert.ok(elements.app.innerHTML.includes("Still a gap"));
click({ "data-tab": "flow" });
assert.ok(elements.app.innerHTML.includes("What comes in, where it goes"));

const hostile = context.ClaimlineFlow.render({
  job_title: "<script>alert(1)</script>",
  covered: [],
  gaps: [],
  checks: {},
  trace: [{ tool: "screen_job", detail: "<script>alert(1)</script>" }],
}, "screen_job");
assert.ok(!hostile.includes("<script>"));
assert.ok(hostile.includes("&lt;script&gt;"));
