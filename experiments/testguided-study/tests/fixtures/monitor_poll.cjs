// Run the shipped script with a minimal DOM and a deterministic network/clock.
const fs = require('node:fs');
const vm = require('node:vm');
const [html, scenario] = process.argv.slice(2);
const elements = new Map();
function element() {
 return {textContent:'', dataset:{}, style:{}, classList:{toggle(){}},
  setAttribute(){}, addEventListener(){}, replaceChildren(){}, append(){},
  contains(){return false;}, querySelectorAll(){return [];}};
}
const document = {
 getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);},
 createElement:element, createTextNode:element, querySelectorAll(){return [];}
};
const terminalScenario=['finished','failed','interrupted','prepared'].includes(scenario);
let timers = new Map(), timerId=0, calls=0, clock, now=200000;
const base={state:'running', started_at:100, updated_at:150, observed_at:200, runs:[], events:[], agent:{}};
const context = {
 document, Option:function(){return element();}, AbortController, console,
 Date:class extends Date {static now(){return now;}},
 setTimeout(fn,delay){timers.set(++timerId,{fn,delay});return timerId;},
 clearTimeout(id){timers.delete(id);}, setInterval(fn){clock=fn;},
 async fetch(){
  calls++;
  if(scenario==='offline' || terminalScenario && calls>1 || scenario==='disconnect' && calls>1 || scenario==='recover' && calls===2)throw Error('connection lost');
  const data=scenario==='malformed'?{runs:[null]}:
   {...base, state:terminalScenario?scenario:scenario==='closing'?'finished':'running', monitor_closing:scenario==='closing'||scenario==='recover'&&calls===3};
  return {ok:true,json:async()=>data};
 }
};
async function settle(){for(let i=0;i<20;i++)await Promise.resolve();}
(async()=>{
 vm.runInNewContext(fs.readFileSync(html,'utf8').split('<script>')[1].split('</script>')[0],context);
 await settle();
 for(let i=0;i<15;i++){
  const entry=[...timers.entries()].find(([,t])=>t.delay===1000);
  if(!entry)break;
  timers.delete(entry[0]);entry[1].fn();await settle();
 }
 now=900000;clock();
 console.log(JSON.stringify({calls, pending:timers.size, connection:document.getElementById('connection').dataset.state,
  detail:document.getElementById('connection-detail').textContent,
  banner:document.getElementById('error-banner').textContent,
  clock:document.getElementById('study-clock').textContent}));
})().catch(error=>{console.error(error);process.exitCode=1;});
