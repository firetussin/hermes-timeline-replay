import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
let source=fs.readFileSync(new URL('../desktop/plugin.js',import.meta.url),'utf8').replace(/^import .*;$/gm,'').replace('export default','globalThis.plugin =');
const requests=[],drafts=[],states=[];let cursor=0;
function Button(){}function Input(){}
const context={useRef:()=>({current:null}),MutationObserver:class{observe(){}disconnect(){}},useMemo:(f)=>f(),navigator:{userAgent:globalThis.UA||''},SDK:{SandboxedFrame:function SandboxedFrame(){},MessageTextContent:function MessageTextContent(){},captureGatewayFileDownload:()=>async()=>{}},ROUTES_AREA:'routes',SIDEBAR_NAV_AREA:'sidebar',Button,Input,
  icons:{Activity:()=>null},host:{state:{profile:{}},notify:()=>{},navigate:url=>navigated.push(url),composer:{insertText:async(...x)=>{drafts.push(x);return true;},focus:()=>{}}},
  h:(tag,props,...children)=>({tag,props:props||{},children:children.flat()}),
  useState:initial=>{const i=cursor++;if(!(i in states))states[i]=typeof initial==='function'?initial():initial;return[states[i],v=>states[i]=typeof v==='function'?v(states[i]):v];},
  useEffect:()=>{},window:{addEventListener(){},removeEventListener(){},location:{reload(){}}},
  useValue:()=> 'Research',useQuery:opts=>({
    isError:opts.queryKey.at(-1)==='status'&&Boolean(globalThis.failStatus),
    data:opts.queryKey.at(-1)==='status'&&globalThis.failStatus?undefined:opts.queryKey.at(-1)==='status'?{version:globalThis.hostVersion,profiles:['current','Research'],renderer_ready:false,dependencies:{items:[{id:'node',label:'Node.js',ready:false,detail:'Not found'}]}}:opts.queryKey.at(-1)==='demo-preview'?{html:'<p>SYNTHETIC SAMPLE</p>'}:{jobs:[]},
    refetch:async()=>{},isLoading:false
  })};
vm.createContext(context);vm.runInContext(source,context);
let contributions=[];
const actionsRun=[];
const opened=[],clipboard=[],navigated=[];
let settingsPage=null;const stored={};
const ctx={registerSettingsPage:pg=>{settingsPage=pg;return()=>{};},listActions:()=>[{id:'profile.default',label:'Default profile'}],runAction:id=>{actionsRun.push(id);return{ok:true};},storage:{get:(k,d)=>k in stored?stored[k]:d,set:(k,v)=>{stored[k]=v;}},addEventListener:()=>()=>{},registerMany:x=>contributions.push(...x),os:{writeClipboard:async x=>{clipboard.push(x);return true;},openExternal:async url=>{opened.push(url);return globalThis.openOk!==false;}},rest:async(path,opts)=>{
  requests.push({path,opts});
  if(opts?.body?.action==='setup')return{prompt:'Install only missing render tools on this connected Hermes host.'};
  return{ok:true,jobs:[]};
}};
context.plugin.register(ctx);assert.equal(context.plugin.id,'timeline-replay');assert.equal(contributions.length,2);
const component=contributions[0].render();
const render=()=>{cursor=0;return component.tag(component.props);};
const flatten=x=>!x||typeof x!=='object'?[]:[x,...(x.children||[]).flatMap(flatten)];
const text=x=>typeof x==='string'?x:(x?.children||[]).map(text).join('');
const find=(tree,t)=>flatten(tree).find(x=>text(x)===t&&(x.tag===Button||x.tag==='button'));
let tree=render();
// Browser (Webapp): SandboxedFrame with a data: URL, so the gateway guest shell runs the scripts.
assert.ok(flatten(tree).some(x=>x.tag===context.SDK.SandboxedFrame&&x.props.src.startsWith('data:text/html')&&decodeURIComponent(x.props.src).includes('SYNTHETIC')));
assert.equal(find(tree,'Render MP4').props.disabled,true);
find(tree,'All available').props.onClick();tree=render();
find(tree,'Create replay').props.onClick();await new Promise(resolve=>setImmediate(resolve));
const build=requests.find(r=>r.opts?.body?.action==='build');
assert.equal(build.opts.body.client_api,1);
assert.match(text(tree),/v0\.5\.3/);
assert.match(text(tree),/Metadata only: no prompts, transcripts or tool results\./);
assert.equal(build.opts.body.range,'all');assert.equal(build.opts.body.pace,'social');assert.equal(build.opts.body.seconds,30);assert.equal(build.opts.body.history,true);
tree=render();await find(tree,'Video setup').props.onClick();tree=render();
assert.equal(find(tree,'Hide video setup').props['aria-expanded'],true);
await find(tree,'Ask Hermes to install missing tools').props.onClick();
assert.equal(drafts.length,1);assert.match(drafts[0][1],/missing render tools/);
assert.equal(drafts[0][2].mode,'block');
assert.ok(!requests.some(r=>r.opts?.body?.action==='install'));
tree=render();find(tree,'Hide video setup').props.onClick();tree=render();
assert.ok(!find(tree,'Ask Hermes to install missing tools'),'header button closes the setup panel');
assert.ok(find(tree,'Video setup'));
globalThis.failStatus=true;tree=render();
assert.match(text(tree),/not running in this profile \(Research\)/);
find(tree,'Switch to Default profile').props.onClick();assert.deepEqual(actionsRun,['profile.default']);
// Native Desktop (Electron): direct srcdoc frame.
globalThis.failStatus=false;context.navigator.userAgent='Mozilla/5.0 Electron/40.0.0';tree=render();
assert.ok(flatten(tree).some(x=>x.tag==='iframe'&&x.props.srcDoc.includes('SYNTHETIC')));
// Settings → Plugins page: registered with four sub-pages; each renders; a default flows to the build.
assert.ok(settingsPage);assert.equal(JSON.stringify(settingsPage.children.map(c=>c.id)),JSON.stringify(['build','export','about']));
for(const pg of [settingsPage,...settingsPage.children]){cursor=0;const tree=pg.render();assert.ok(tree&&typeof tree.tag==='function');cursor=0;tree.tag(tree.props);}
stored.defaults={...(stored.defaults||{}),resolution:'720p',eventsLimit:50000};
for(const k of Object.keys(states))delete states[k];globalThis.failStatus=false;requests.length=0;context.navigator.userAgent='';
tree=render();find(tree,'Create replay').props.onClick();await new Promise(r=>setImmediate(r));
const b2=requests.find(r=>r.opts?.body?.action==='build');assert.equal(b2.opts.body.resolution,'720p');assert.equal(b2.opts.body.events_limit,50000);
// Version notice: Hermes refuses hermes:// links from inside the app, so the notice sends the user to
// Capabilities → Plugins (host.navigate) and only offers the link and the host command for copying.
const notice=t=>flatten(t).find(x=>x.tag?.name==='VersionNotice');
const showNotice=()=>{cursor=0;const t=render();const n=notice(t);if(!n)return null;cursor=500;return n.tag(n.props);};
for(const k of Object.keys(states))delete states[k];
assert.equal(notice(render()),undefined,'no notice when versions match or host version unknown');
globalThis.hostVersion='9.9.9';let nt=showNotice();
assert.match(text(nt),/v9\.9\.9 is on the Hermes host; this Desktop page is v0\.5\.3/);assert.match(text(nt),/Capabilities → Plugins/);
find(nt,'Open Plugins').props.onClick();assert.deepEqual(navigated,['/capabilities?tab=plugins']);
await find(nt,'Copy update link').props.onClick();assert.equal(clipboard.at(-1),'hermes://plugin/install?catalog=timeline-replay');
nt=showNotice();assert.ok(find(nt,'Link copied'));
for(const k of Object.keys(states))delete states[k];globalThis.hostVersion='0.2.9';nt=showNotice();
assert.match(text(nt),/newer than the plugin on the Hermes host \(v0\.2\.9\)/);assert.match(text(nt),/hermes plugins update timeline-replay && hermes gateway restart/);
await find(nt,'Copy host command').props.onClick();assert.equal(clipboard.at(-1),'hermes plugins update timeline-replay && hermes gateway restart');
assert.deepEqual(opened,[],'never tries to open hermes:// from inside the app');
assert.ok(!requests.some(r=>r.opts?.body?.action==='install'),'the plugin never installs anything itself');
globalThis.hostVersion=undefined;
// Style picker: a canvas style hides Pacing and builds with that pace; Timeline brings Pacing back.
for(const k of Object.keys(states))delete states[k];requests.length=0;tree=render();
assert.ok(find(tree,'Balanced'),'Pacing shown for Timeline');find(tree,'Galaxy').props.onClick();tree=render();
assert.ok(!find(tree,'Balanced'),'Pacing hidden for canvas styles');find(tree,'Create replay').props.onClick();await new Promise(r=>setImmediate(r));
assert.equal(requests.find(r=>r.opts?.body?.action==='build').opts.body.pace,'galaxy');
tree=render();find(tree,'Timeline').props.onClick();tree=render();assert.ok(find(tree,'Balanced'),'Pacing back for Timeline');
console.log('Desktop: settings page (4 pages) + defaults to build, Webapp guest frame + Electron srcdoc frame, other-profile state + switch action, native controls, sample preview, all-time/social build payload, setup draft without installation, setup toggle, version label, client_api, render readiness guard, version notice (Desktop-only install link, fallback, newer-page case) passed.');
