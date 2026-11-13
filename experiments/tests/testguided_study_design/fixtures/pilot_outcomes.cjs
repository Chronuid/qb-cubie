// Feed outcome transitions through the shipped monitor's polling and table DOM.
const fs = require('node:fs');
const vm = require('node:vm');
const states = JSON.parse(fs.readFileSync(0, 'utf8'));
const elements = new Map();
function element() {
  return {textContent: '', value: '', dataset: {}, style: {}, children: [],
    classList: {toggle() {}}, setAttribute() {}, addEventListener() {},
    append(...items) { this.children.push(...items); },
    replaceChildren(...items) { this.children = items; },
    contains() { return false; }, querySelectorAll() { return []; }};
}
const document = {
  getElementById(id) {
    if (!elements.has(id)) elements.set(id, element());
    return elements.get(id);
  },
  createElement: element,
  createTextNode(value) { return {...element(), textContent: String(value)}; },
  querySelectorAll() { return []; }
};
const timers = new Map();
let timerId = 0, calls = 0;
const context = {
  document, AbortController, console, Date,
  Option: function(label, value) { return {...element(), textContent: label, value}; },
  setTimeout(fn, delay) { timers.set(++timerId, {fn, delay}); return timerId; },
  clearTimeout(id) { timers.delete(id); }, setInterval() {},
  async fetch() {
    if (calls >= states.length) throw Error('Unexpected extra state request');
    const state = states[calls++];
    return {ok: true, json: async () => state};
  }
};
async function settle() { for (let i = 0; i < 50; i++) await Promise.resolve(); }
function outcome() {
  const row = document.getElementById('runs').children[0];
  if (!row || row.children.length !== 6) throw Error('Expected one rendered run row');
  return {result: row.children[4].textContent, elapsed: row.children[5].textContent,
    unavailable: document.getElementById('unavailable').textContent,
    failed: document.getElementById('failed').textContent};
}
(async () => {
  const script = fs.readFileSync(process.argv[2], 'utf8').split('<script>')[1].split('</script>')[0];
  vm.runInNewContext(script, context);
  await settle();
  const views = [outcome()];
  for (let i = 1; i < states.length; i++) {
    const entry = [...timers.entries()].find(([, timer]) => timer.delay === 1000);
    if (!entry) throw Error('Monitor did not schedule its next poll');
    timers.delete(entry[0]);
    entry[1].fn();
    await settle();
    views.push(outcome());
  }
  console.log(JSON.stringify(views));
})().catch(error => { console.error(error); process.exitCode = 1; });
