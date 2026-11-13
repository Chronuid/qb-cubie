// Execute the shipped page against its actual element IDs, not invented nodes.
const fs = require('node:fs');
const vm = require('node:vm');
const [path, scenario] = process.argv.slice(2);
const html = fs.readFileSync(path, 'utf8');
const elements = new Map();
function element(attributes = {}) {
  const classes = new Set();
  return {textContent: '', value: '', dataset: {}, style: {}, children: [], listeners: {},
    scrollTop: 0, scrollLeft: 0, disabled: false, hidden: false,
    classList: {toggle(name, force) { if (force) classes.add(name); else classes.delete(name); },
      contains(name) { return classes.has(name); }},
    getAttribute(name) { return attributes[name] ?? null; },
    setAttribute(name, value) { attributes[name] = value; },
    append(...items) { this.children.push(...items); },
    replaceChildren(...items) { this.children = items; },
    addEventListener(name, callback) { this.listeners[name] = callback; },
    contains() { return false; }, querySelectorAll() { return []; }};
}
for (const match of html.matchAll(/<[^>]+\bid="([^"]+)"[^>]*>/g)) {
  const attributes = Object.fromEntries([...match[0].matchAll(/([\w-]+)="([^"]*)"/g)].map(m => [m[1], m[2]]));
  elements.set(match[1], element(attributes));
}
const document = {
  getElementById(id) { return elements.get(id) || null; },
  createElement() { return element(); },
  createTextNode(value) { return {...element(), textContent: String(value)}; },
  querySelectorAll(selector) {
    return selector === '.tab' ? [...elements.values()].filter(e => e.getAttribute('role') === 'tab') : [];
  }
};
const timers = new Map(), copied = [], archiveQueries = [];
let timerId = 0, stateCalls = 0;
const sent = index => [
  {role: 'system', content: 'FRAMEWORK_GUIDE'},
  {role: 'user', content: `CONTEXT_${index} · café </script>`},
  {role: 'assistant', content: 'ACTION_ALREADY_SENT_IN_CONTEXT'}
];
const unsent = {action: {reason: 'UNSENT_ACTION'}, result: {stdout: 'UNSENT_TOOL'},
  response: {raw: 'UNSENT_RESPONSE'}};
const context = {
  document, AbortController, console, Date,
  Option: function(label, value) { return {...element(), textContent: label, value}; },
  navigator: {clipboard: {async writeText(value) { copied.push(value); }}},
  setTimeout(fn, delay) { timers.set(++timerId, {fn, delay}); return timerId; },
  clearTimeout(id) { timers.delete(id); }, setInterval() {},
  async fetch(url) {
    if (url.startsWith('/api/run')) {
      const params = new URL(url, 'http://monitor.local').searchParams;
      const step = params.has('step') ? Number(params.get('step')) : stateCalls - 1;
      archiveQueries.push(params.get('step'));
      return {ok: true, json: async () => ({step, steps: [0, 1],
        agent: {...unsent, context: sent(`ARCHIVE_${step}`)}})};
    }
    const index = stateCalls++;
    const agent = {...unsent, context: sent(index)};
    if (scenario === 'missing') delete agent.context;
    if (scenario === 'empty') agent.context = [];
    if (scenario === 'malformed') agent.context = {content: 'NOT_A_SENT_MESSAGE_ARRAY'};
    if (scenario === 'error') {
      agent.last_error = {error: 'Invalid JSON action', status: 'invalid_output', step: 2,
        raw: 'UNSENT_RAW_ERROR', usage: {output_tokens: 8192}};
      agent.stop_reason = 'invalid_output';
    }
    return {ok: true, json: async () => ({state: 'model_wait', phase: 'running',
      active: {run_id: '0001', step: index, operation: 'model'},
      runs: [{run_id: '0001', task_id: 'example', mode: 'pytest', status: 'running'}], events: [], agent})};
  }
};
async function settle() { for (let i = 0; i < 50; i++) await Promise.resolve(); }
async function event(id, name, value) {
  const target = document.getElementById(id);
  if (value !== undefined) target.value = value;
  await target.listeners[name]({target});
  await settle();
}
async function poll() {
  const entry = [...timers.entries()].find(([, timer]) => timer.delay === 1000);
  if (!entry) throw Error('Monitor did not schedule its next poll');
  timers.delete(entry[0]); entry[1].fn(); await settle();
}
const payload = () => document.getElementById('payload').textContent;
(async () => {
  vm.runInNewContext(html.split('<script>')[1].split('</script>')[0], context);
  await settle();
  const initial = payload();
  let paused, resumed, archived;
  if (scenario === 'pause') {
    await event('pause', 'click'); await poll(); paused = payload();
    await event('pause', 'click'); resumed = payload();
  } else if (scenario === 'archive' || scenario === 'copy-archive') {
    await event('run-select', 'change', '0001');
    await event('step-select', 'change', '0');
    archived = payload(); await poll();
    if (payload() !== archived) throw Error('Pinned context changed during polling');
    if (scenario === 'archive') await event('run-select', 'change', '');
  } else if (scenario === 'live' || scenario === 'wrap') {
    if (scenario === 'wrap') {
      document.getElementById('payload').scrollTop = 123;
      document.getElementById('payload').scrollLeft = 17;
      await event('wrap', 'click');
    }
    await poll();
  }
  await event('copy', 'click');
  const reset = [...timers.entries()].find(([, timer]) => timer.delay === 1600);
  if (reset) { timers.delete(reset[0]); reset[1].fn(); }
  const output = document.getElementById('payload');
  console.log(JSON.stringify({initial, payload: payload(), paused, resumed, archived, copied,
    copyDisabled: document.getElementById('copy').disabled,
    copyLabel: document.getElementById('copy').textContent,
    empty: output.classList.contains('is-empty'), noWrap: output.classList.contains('no-wrap'),
    scrollTop: output.scrollTop, scrollLeft: output.scrollLeft, archiveQueries, stateCalls,
    errorNote: document.getElementById('last-error-note').textContent,
    stopNote: document.getElementById('agent-stop-note').textContent}));
})().catch(error => { console.error(error); process.exitCode = 1; });
