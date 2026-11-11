// Render the actual Desktop component through a tiny SDK/VDOM fixture. This is a
// design preview, not a claim that the native Hermes app was driven in this test.
import fs from 'node:fs';
import vm from 'node:vm';
const sample=fs.readFileSync(new URL('../demo/replay.html',import.meta.url),'utf8');
const states=[];let cursor=0;
const h=(tag,props,...children)=>({tag,props:props||{},children:children.flat()});
function Button(props){return h('button',{...props,className:'sdk-button '+(props.variant||'default')},...props.children);}
function Input(props){return h('input',{...props,className:'sdk-input'});}
const profileNames=['current','ChasingAces','EVE','Forge','Library','Researchbot','Researcher','Scout','Office','Sonny','YouTube'];
const deps={ready:false,items:[{id:'node',label:'Node.js 22+',ready:true,detail:'v22.20.0'},{id:'hyperframes',label:'HyperFrames',ready:false,detail:'Not configured'},{id:'ffmpeg',label:'FFmpeg',ready:true,detail:'On PATH'},{id:'ffprobe',label:'ffprobe',ready:true,detail:'On PATH'},{id:'browser',label:'Chrome / Chromium',ready:true,detail:'Detected'}]};
const context={h,Button,Input,ROUTES_AREA:'routes',SIDEBAR_NAV_AREA:'sidebar',host:{state:{profile:{}}},
icons:{Activity:({size=14})=>h('svg',{width:size,height:size,viewBox:'0 0 24 24',fill:'none',stroke:'currentColor','stroke-width':1.7},h('path',{d:'M3 12h4l3-8 4 16 3-8h4'}))},
useValue:()=> 'Research',useState:initial=>{let i=cursor++;if(!(i in states))states[i]=initial;return[states[i],v=>states[i]=typeof v==='function'?v(states[i]):v];},
useQuery:opts=>({data:opts.queryKey.at(-1)==='status'?{profiles:profileNames,renderer_ready:false,dependencies:deps}:opts.queryKey.at(-1)==='demo-preview'?{html:sample}:{jobs:[]},refetch:async()=>{}})};
const source=fs.readFileSync(new URL('../desktop/plugin.js',import.meta.url),'utf8').replace(/^import .*;$/gm,'').replace('export default','globalThis.plugin =');
vm.createContext(context);vm.runInContext(source,context);let registered=[];
context.plugin.register({registerMany:x=>registered.push(...x),rest:async()=>({prompt:'Set up only missing render dependencies on this connected Hermes host.'})});
const page=registered[0].render();cursor=0;const tree=page.tag(page.props);
const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const cssName=s=>s.replace(/[A-Z]/g,c=>'-'+c.toLowerCase());
function markup(n){
 if(n===null||n===undefined||n===false)return'';
 if(typeof n!=='object')return escape(n);
 if(Array.isArray(n))return n.map(markup).join('');
 if(typeof n.tag==='function')return markup(n.tag({...n.props,children:n.children}));
 const attrs=[];
 for(const [key,value] of Object.entries(n.props)){
  if(key.startsWith('on')||value===undefined||value===null||value===false||key==='key')continue;
  if(key==='style'){attrs.push('style="'+escape(Object.entries(value).map(([k,v])=>cssName(k)+':'+(typeof v==='number'&&!['opacity','fontWeight','flex','zIndex'].includes(k)?v+'px':v)).join(';'))+'"');continue;}
  const name={className:'class',srcDoc:'srcdoc',readOnly:'readonly'}[key]||key;
  attrs.push(name+'="'+escape(name.startsWith('aria-')?String(value):value===true?'':value)+'"');
 }
 const inner=n.tag==='style'?n.children.join(''):n.children.map(markup).join('');
 return '<'+n.tag+' '+attrs.join(' ')+'>'+inner+(['input','br','img'].includes(n.tag)?'':'</'+n.tag+'>');
}
const wrapper=`<!doctype html><html lang="en" data-theme="dark"><meta charset="utf-8"><title>Timeline Replay — Desktop design preview</title><style>
:root{--ui-text-primary:#e7e8ec;--ui-text-secondary:#b5b7c2;--ui-text-tertiary:#9295a5;--ui-text-quaternary:#70758a;--ui-stroke-secondary:#30333f;--ui-accent:#a596ed;--ui-bg-primary:#171821;--ui-bg-secondary:#1d1f2a;--ui-bg-quaternary:#292c3a}
:root[data-theme=light]{--ui-text-primary:#242531;--ui-text-secondary:#555968;--ui-text-tertiary:#6a7082;--ui-text-quaternary:#7e8391;--ui-stroke-secondary:#d6d9e1;--ui-accent:#6553bf;--ui-bg-primary:#fafafd;--ui-bg-secondary:#f1f2f7;--ui-bg-quaternary:#e6e8f0}*{box-sizing:border-box}body{margin:0;background:var(--ui-bg-primary);color:var(--ui-text-primary);font:13px system-ui,sans-serif}.fixture-bar{padding:10px 20px;border-bottom:1px solid var(--ui-stroke-secondary);display:flex;gap:12px;align-items:center;color:var(--ui-text-tertiary);font-size:11px}.sdk-button{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:7px 11px;border:1px solid transparent;border-radius:4px;font:500 12px/1.4 system-ui,sans-serif;background:var(--ui-accent);color:var(--ui-bg-primary);cursor:pointer}.sdk-button.outline{background:transparent;color:var(--ui-text-primary);border-color:var(--ui-stroke-secondary)}.sdk-button.text,.sdk-button.ghost{background:transparent;color:var(--ui-text-secondary)}.sdk-button:disabled{opacity:.45;cursor:default}.sdk-input{width:100%;background:var(--ui-bg-primary);border:1px solid var(--ui-stroke-secondary);color:var(--ui-text-primary);padding:8px;border-radius:4px}.tr-page{height:auto!important}
</style><div class="fixture-bar">DESKTOP DESIGN PREVIEW · Mock Hermes SDK and synthetic data <button class="sdk-button outline" onclick="document.documentElement.dataset.theme='dark'">Dark</button><button class="sdk-button outline" onclick="document.documentElement.dataset.theme='light'">Light</button></div>`+markup(tree)+`</html>`;
fs.writeFileSync(new URL('../demo/desktop-preview.html',import.meta.url),wrapper);
console.log('Wrote mocked-SDK Desktop design preview from the real component source.');
