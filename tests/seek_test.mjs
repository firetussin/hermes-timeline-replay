// Offline DOM/animation harness: no browser, network or real profile access.
// Executes the actual artwork initialization and scrubs a full loop plus reverse seeks.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const path=process.argv[2];
if(!path)throw new Error('Pass the generated replay.html path');
const html=fs.readFileSync(path,'utf8');
const data=JSON.parse(html.match(/id="replay-data">([\s\S]*?)<\/script>/)[1]);
const settings=JSON.parse(html.match(/id="replay-settings">([\s\S]*?)<\/script>/)[1]);
settings.interactive=false;
class Element {
  constructor(tag='div'){this.tagName=tag;this.children=[];this.style={};this.dataset={};this.clientWidth=1920;this.textContent='';}
  appendChild(x){this.children.push(x);return x;}
  animate(frames,opts){const a={frames,opts,currentTime:0,pause(){}};animations.push(a);return a;}
}
const animations=[],root=new Element(),ids={root};
ids['replay-data']={textContent:JSON.stringify(data)};ids['replay-settings']={textContent:JSON.stringify(settings)};
const context={document:{getElementById:id=>ids[id],createElement:tag=>new Element(tag),createTextNode:t=>({textContent:t})},window:{},Intl,Map,Set,Math,Date,Number,Array,JSON};
vm.createContext(context);
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
vm.runInContext(scripts.at(-1)[1],context,{timeout:10000});
const api=context.window.TimelineReplay;
for(const e of data.events)assert.ok(Math.abs(api.realAt(api.videoAt(e.offset))-e.offset)<.001,'Pacing map round-trip must preserve actual event time');
for(let i=0;i<=Math.ceil(api.duration*30);i++)api.seek(i/30);
const snap=t=>{api.seek(t);return JSON.stringify({times:animations.map(a=>a.currentTime),visible:root.children.map(c=>c.style.visibility)});};
const expected=snap(12.34);api.seek(api.duration);api.seek(0);assert.equal(snap(12.34),expected);
api.seek(api.duration);assert.equal(root.children.at(-1).style.visibility,'visible');
assert.equal(api.data.totals.tools,data.events.filter(e=>e.kind==='tool').length);
// Orbit draws its body on a canvas (seek/hf-seek); the lane paces build many WAAPI animations.
if(settings.canvas)assert.ok(root.children.some(c=>String(c.className).includes('orbit-scene')),settings.pace+' canvas scene present');else assert.ok(animations.length>50);
assert.ok(root.children.length>=2);
for(let p=0;p<api.chapters;p++){
 api.seek((p+.5)*settings.seconds/api.chapters);
 assert.equal(root.children[p].style.visibility,'visible');
 assert.equal(root.children.filter(x=>x.style.visibility==='visible').length,1);
}
console.log(JSON.stringify({ok:true,duration:api.duration,chapters:api.chapters,animations:animations.length,frames:Math.ceil(api.duration*30)+1,reverseSeek:true}));
