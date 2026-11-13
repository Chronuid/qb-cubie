// Exercise the actual monitor, including archive selection, without a browser.
const fs = require('node:fs');
const vm = require('node:vm');
const [html, scenario] = process.argv.slice(2);
const elements = new Map();
function element() {
 return {textContent:'', value:'', dataset:{}, style:{}, children:[], listeners:{},
  classList:{toggle(){}}, setAttribute(){}, append(...items){this.children.push(...items);},
  addEventListener(name, callback){this.listeners[name]=callback;},
  replaceChildren(...items){this.children=items;}, contains(){return false;},
  querySelectorAll(){return [];}};
}
const document = {
 getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);},
 createElement:element, createTextNode:element, querySelectorAll(){return [];}
};
const timers = new Map();
let timerId=0, stateCalls=0, archiveCalls=0;
const archiveQueries=[];
const context = {
 document, Option:function(label,value){return {...element(),textContent:label,value};},
 AbortController, console, Date,
 setTimeout(fn,delay){timers.set(++timerId,{fn,delay});return timerId;},
 clearTimeout(id){timers.delete(id);}, setInterval(){},
 async fetch(url){
  if(url.startsWith('/api/run')) {
   archiveCalls++;
   const query=new URL(url,'http://monitor.local').searchParams;
   const step=query.has('step')?Number(query.get('step')):stateCalls>=2?1:0;
   archiveQueries.push(query.get('step'));
   return {ok:true,json:async()=>({step,steps:stateCalls>=2?[0,1]:[0],
    agent:{context:[{role:'user',content:step===0?'CONTEXT_ZERO':'CONTEXT_ONE'}]}})};
  }
  stateCalls++;
  return {ok:true,json:async()=>({state:'model_wait',phase:'running',
   active:{run_id:'0001',step:stateCalls>=2?1:0,operation:'model'},
   runs:[{run_id:'0001',mode:'pytest',task_id:'example',status:'running'}],
   events:[],agent:{context:[{role:'user',content:'LIVE_CONTEXT'}]}})};
 }
};
async function settle(){for(let i=0;i<50;i++)await Promise.resolve();}
async function select(id,value){const node=document.getElementById(id);node.value=value;node.listeners.change({target:node});await settle();}
(async()=>{
 vm.runInNewContext(fs.readFileSync(html,'utf8').split('<script>')[1].split('</script>')[0],context);
 await settle();
 await select('run-select','0001');
 if(scenario==='pinned')await select('step-select','0');
 const poll=[...timers.entries()].find(([,timer])=>timer.delay===1000);
 if(!poll)throw Error('Monitor did not schedule its next poll');
 timers.delete(poll[0]);poll[1].fn();await settle();
 console.log(JSON.stringify({stateCalls,archiveCalls,archiveQueries,
  stepLabel:document.getElementById('step-stage').textContent,
  payload:document.getElementById('payload').textContent,
  steps:document.getElementById('step-select').children.map(option=>option.value)}));
})().catch(error=>{console.error(error);process.exitCode=1;});
