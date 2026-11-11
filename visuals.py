"""Same seekable WAAPI artwork in interactive HTML and HyperFrames exports."""
import json
import math
import secrets
import time
from pathlib import Path

from .core import data_dir, number
from . import presentation

CSS = r'''
:root{color-scheme:dark}*{box-sizing:border-box}html,body{margin:0;background:#080e1e;color:#f0f3ff;font-family:system-ui,sans-serif}#root{position:relative;width:100%;height:100%;overflow:hidden;background:#080e1e}.scene{position:absolute;inset:0;padding:64px 76px;background:radial-gradient(ellipse at 90% 0%,#17284b,#080e1e 70%)}.eyebrow{font:600 17px ui-monospace,monospace;letter-spacing:5px;color:#99b3d4}.heading{display:flex;align-items:flex-start;justify-content:space-between;gap:36px;margin-top:16px}h1{font-size:54px;line-height:1.12;max-width:1200px;margin:0;letter-spacing:-2px}.chapter{color:#b4c4dd;font-size:20px;margin-top:16px}.clock{padding:18px 24px;border:1px solid #ff7869;background:#341b2b;border-radius:16px;color:#ffc1b5;font:600 23px ui-monospace,monospace;min-width:285px;min-height:98px}.clock small{display:block;margin-top:10px;font-size:14px;color:#efc2bd}.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:18px;margin-top:30px;height:106px}.stat{background:#111d34;border:1px solid #2b3f5d;border-radius:12px;padding:15px 20px}.stat b{display:block;font-size:38px;line-height:1.12}.stat span{font:13px ui-monospace,monospace;color:#adc1df;text-transform:uppercase;letter-spacing:2px}.plot{position:relative;height:518px;margin-top:24px}.labels{position:absolute;inset:20px auto 0 0;width:250px}.lane-label{height:58px;display:flex;align-items:center;padding-right:20px;font-size:19px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.axis{position:absolute;left:265px;right:0;top:20px;height:464px}.gridline{position:absolute;top:0;bottom:0;border-left:1px solid #263952}.tick{position:absolute;top:-23px;font:13px ui-monospace,monospace;color:#9fb6d8;transform:translateX(-50%)}.lane-bg{position:absolute;left:0;right:0;height:44px;background:#101d31;border-radius:6px;border:1px solid #1e304c}.band{position:absolute;top:0;bottom:0;background:#6e8dc414;border-left:1px solid #55729d33}.band-label{position:absolute;bottom:-22px;font:12px ui-monospace,monospace;color:#9fb6d8}.mark{position:absolute;display:block;height:14px;min-width:5px;border-radius:5px;transform-origin:left center;opacity:0}.dot{width:9px;height:9px;border-radius:50%;box-shadow:0 0 14px currentColor}.event-title{pointer-events:none}.playhead{position:absolute;left:0;top:0;bottom:0;width:2px;background:#ffd074;box-shadow:0 0 16px #ffd07466}.playhead:before{content:"";position:absolute;top:-5px;left:-4px;width:10px;height:10px;background:#ffd074;transform:rotate(45deg)}.ticker{display:flex;gap:22px;align-items:center;border-top:1px solid #304563;padding-top:22px;height:78px}.ticker-key{color:#ffd074;font:14px ui-monospace,monospace;letter-spacing:2px;flex-shrink:0}.ticker-copy{font-size:24px;line-height:1.3}.footer{position:absolute;bottom:25px;left:76px;right:76px;display:flex;justify-content:space-between;color:#9fb6d8;font:13px ui-monospace,monospace;gap:30px}.demo-tag{color:#ffd074}.snapshot{position:absolute;inset:0;opacity:0}.stat-stack{position:relative;height:106px;margin-top:30px}.stat-stack .stats{margin-top:0}.clock-stack{position:relative;width:300px;height:100px;flex-shrink:0}.clock-stack .snapshot{inset:0}.ticker-stack{position:relative;height:45px;flex:1}.closing{display:flex;flex-direction:column;justify-content:center}.closing h1{font-size:88px;max-width:1450px;margin:32px 0}.closing .stats{height:130px}.closing .stat b{font-size:50px}.closing-note{margin-top:36px;color:#b4c4dd;font-size:23px;line-height:1.5;max-width:1500px}.closing-date{margin-top:22px;color:#ffd074;font:21px ui-monospace,monospace}.artifact-shell{width:min(100vw,1400px);margin:auto}.viewport{width:100%;aspect-ratio:16/9;position:relative;overflow:hidden}.viewport #root{position:absolute;width:1920px;height:1080px;transform-origin:top left}.controls{padding:15px;display:flex;align-items:center;gap:13px;flex-wrap:wrap;background:#111d34;border-top:1px solid #304563}.controls button,.controls select{background:#223853;color:#fff;border:1px solid #547195;border-radius:7px;padding:9px 14px;font:inherit}.controls input{flex:1;min-width:120px;accent-color:#ffd074}.controls output{font:13px ui-monospace,monospace}.details{padding:18px;color:#b4c4dd;font-size:14px;line-height:1.6}.details summary{cursor:pointer;color:#ffd074}.empty{padding:80px}.legend{display:flex;gap:22px;margin-top:12px;color:#adc1df;font:13px ui-monospace,monospace}.legend i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}.source-note{max-width:1150px}
'''

CSS += r'''
.scene{background:radial-gradient(ellipse at 85% 10%,#182756,#080e1e 60%)}.heading h1{font-size:58px;font-weight:800}.eyebrow{color:#b8c4ff}.stat b{font-size:44px;font-variant-numeric:tabular-nums;letter-spacing:-1px}.stat span{font-size:15px;letter-spacing:1.2px}.stat{border-color:#354877}.lane-label{font-size:23px;font-weight:600}.tick{font-size:16px}.chapter{font-size:18px}.mark{box-shadow:0 0 14px currentColor}.ticker-copy{font-size:32px;font-weight:650}.ticker-key{font-size:15px}.footer{font-size:14px}.legend{font-size:15px}.playhead{width:3px;box-shadow:0 0 28px #ffd074aa}.event-ring{position:absolute;width:20px;height:20px;border:2px solid currentColor;border-radius:50%;pointer-events:none;opacity:0;z-index:6}.event-spark{position:absolute;width:5px;height:5px;border-radius:2px;opacity:0;pointer-events:none;z-index:7}.lane-flash{position:absolute;left:0;right:0;height:44px;border-radius:6px;pointer-events:none;opacity:0;z-index:2}.packet{position:absolute;width:8px;height:8px;border-radius:50%;box-shadow:0 0 20px currentColor;opacity:0;z-index:9;pointer-events:none}.milestone{position:absolute;right:76px;top:10px;font:800 26px system-ui,sans-serif;color:#080e1e;background:#ffd074;padding:12px 18px;border-radius:10px;opacity:0;z-index:12}.intro{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center;background:radial-gradient(ellipse at 50% 50%,#253873,#080e1e 72%);z-index:15;pointer-events:none}.intro .intro-title{font:850 100px/1 system-ui,sans-serif;letter-spacing:-5px;text-align:center;max-width:1600px}.intro .intro-detail{font:600 24px ui-monospace,monospace;color:#b5c8ff;margin-top:26px;letter-spacing:2px}.closing h1{font-size:120px;font-weight:850;letter-spacing:-5px;margin:24px 0}.closing .stat b{font-size:58px}.closing .stats{height:145px}.closing-note{font-size:22px}.closing-date{font:22px system-ui,sans-serif;color:#b5c8ff}.intro-rule{width:160px;height:5px;background:#ffd074;margin-bottom:38px}.motion-note{font:14px ui-monospace,monospace;color:#b4c4dd}
'''

CSS += r'''
.activity-stage{position:absolute;left:0;right:0;top:0;height:235px}.activity-heading{position:absolute;left:0;top:-5px;font:600 14px ui-monospace,monospace;letter-spacing:3px;color:#adc1df}.activity-hub{position:absolute;left:50%;top:48%;width:126px;height:126px;border:1px solid #a7b9ff;border-radius:50%;transform:translate(-50%,-50%);display:flex;align-items:center;justify-content:center;flex-direction:column;background:radial-gradient(circle,#405aa0,#142343 70%);box-shadow:0 0 70px #6a81ff44;z-index:4}.activity-hub strong{font:850 52px/1 system-ui,sans-serif;color:#edf3ff}.activity-hub small{font:10px ui-monospace,monospace;color:#c9d5ff;letter-spacing:2px;margin-top:8px}.profile-node{position:absolute;transform:translate(-50%,-50%);width:270px;height:68px;z-index:3}.profile-node-inner{height:100%;border:1px solid currentColor;border-radius:14px;padding:12px 17px;background:#111d34;display:flex;align-items:center;gap:13px;position:relative;overflow:hidden}.profile-node-letter{font:800 28px system-ui,sans-serif;min-width:32px}.profile-node-name{font:700 24px system-ui,sans-serif;max-width:175px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.profile-node-id{font:12px ui-monospace,monospace;opacity:.7;margin-top:3px}.signal-route{position:absolute;height:1px;transform-origin:left center;background:#51669277;z-index:0}.node-flash{position:absolute;inset:0;border-radius:14px;opacity:0;pointer-events:none;z-index:0}.hub-wave{position:absolute;left:50%;top:48%;width:126px;height:126px;border:2px solid currentColor;border-radius:50%;margin-left:-63px;margin-top:-63px;opacity:0;pointer-events:none;z-index:2}.activity-readout{position:absolute;left:30%;right:30%;top:191px;text-align:center;font:750 22px/1.1 system-ui,sans-serif;min-height:25px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.social-scene .labels{top:286px}.social-scene .axis{top:286px;height:190px}.social-scene .lane-label{height:46px;font-size:20px}.social-scene .lane-bg{height:36px}.social-scene .plot{height:518px}.heading>div:first-child{min-width:0}.heading h1{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:1180px}
'''

CSS += '.heading h1{line-height:1.3;padding-bottom:2px}.profile-node-id{color:#e0e8ff;opacity:1}'
# 0.2.1 export layout gate: ticks never wrap, lane labels split name/scope, and
# decorative bursts are clipped to the plot so they cannot cover labels or ticks.
CSS += ('.tick{white-space:nowrap}'
        '.fx-layer{position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:6}.marks-layer{position:absolute;inset:0;pointer-events:none}'
        '.lane-label{flex-direction:column;align-items:flex-start;justify-content:center;gap:2px}'
        '.lane-name{display:block;white-space:nowrap;line-height:1.1}'
        '.lane-sub{display:block;font:600 12px/1.2 ui-monospace,monospace;letter-spacing:1.5px;color:#adc1df;text-transform:uppercase;white-space:nowrap}'
        # 0.2.2: card text above the glow; model readouts swap in place; switch markers.
        '.profile-node-inner>*:not(.node-flash){position:relative;z-index:1}'
        '.swap{position:relative;height:15px;width:100%}.swap>.snapshot{white-space:nowrap}'
        '.lane-sub.swap{width:222px;text-transform:none;letter-spacing:.5px}'
        '.model-switch{position:absolute;width:10px;height:10px;margin-left:-5px;background:#e2c7ff;border:1px solid #080e1e;transform:rotate(45deg);z-index:4;opacity:0}'
        '.closing-models{margin-top:14px;color:#e2c7ff;font:600 21px ui-monospace,monospace;white-space:nowrap}'
        '.intro-copy{display:flex;flex-direction:column;align-items:center}')
CSS += ('.social-compact>.eyebrow{position:absolute;top:34px;left:76px;font-size:13px;letter-spacing:4px}.social-compact>.heading{position:absolute;top:54px;left:76px;right:76px;margin:0;align-items:center}.social-compact .heading h1{font-size:40px;line-height:1.15;max-width:1180px}.social-compact .chapter{margin-top:2px;font-size:16px}.social-compact .clock-stack{height:72px;width:280px}.social-compact .clock{min-height:72px;min-width:260px;padding:12px 20px;font-size:21px}.social-compact .clock small{margin-top:6px;font-size:13px}.social-compact>.stat-stack{position:absolute;top:140px;left:76px;right:76px;height:70px;margin:0}.social-compact .stats{height:70px}.social-compact .stat{padding:8px 18px}.social-compact .stat b{font-size:30px}.social-compact .stat span{font-size:12px}.social-compact>.legend{position:absolute;top:220px;left:76px;right:76px;margin:0}.social-compact>.plot{position:absolute;top:246px;left:76px;right:76px;height:700px;margin:0}.social-compact>.ticker{position:absolute;top:950px;left:76px;right:76px;height:56px;border-top:0;padding-top:0}.social-compact .activity-stage{height:110px}.social-compact .activity-heading{display:none}.social-compact .activity-hub{top:50%;width:84px;height:84px}.social-compact .activity-hub strong{font-size:34px}.social-compact .activity-hub small{font-size:10px;margin-top:3px;letter-spacing:1.5px}.social-compact .hub-wave{top:50%;width:84px;height:84px;margin-left:-42px;margin-top:-42px}.social-compact .profile-node{width:250px;height:46px}.social-compact .profile-node-inner{padding:6px 12px;gap:10px;border-radius:11px}.social-compact .profile-node-letter{font-size:22px;min-width:24px}.social-compact .profile-node-name{font-size:20px;max-width:180px}.social-compact .profile-node-id{font-size:11px;margin-top:1px}.social-compact .milestone{top:4px;font-size:19px;padding:7px 14px;border-radius:8px}.social-compact .activity-readout{left:auto;right:0;top:40px;width:560px;text-align:right;font-size:20px}')

CSS += ('.orbit-scene{padding:0;background:radial-gradient(ellipse at 36% 50%,#151a36 0%,#080a14 42%,#05060b 75%)}.orbit-canvas{position:absolute;left:0;top:0;width:1920px;height:1080px}'
        '.orbit-head{position:absolute;left:64px;top:34px;width:880px}.orbit-eyebrow{color:#8d96b8;font:600 13px ui-monospace,monospace;letter-spacing:4px}'
        '.orbit-title{margin:6px 0 4px;font-size:34px;line-height:1.15;font-weight:700;color:#f2f4ff;white-space:nowrap}.orbit-sub{color:#9aa3c4;font:500 14px ui-monospace,monospace;white-space:nowrap}')

JS = r'''
(() => {
"use strict";
const D=JSON.parse(document.getElementById("replay-data").textContent);
const settings=JSON.parse(document.getElementById("replay-settings").textContent);
const root=document.getElementById("root"), anims=[], clips=[], drawers=[];
const palette=["#77c9ff","#b6a0ff","#7ee3b0","#ffbd79","#ef9dc9","#a9de78","#87dbe0","#e5bdff"];
const social=settings.pace==="social", energetic=settings.pace!=="linear";
// Lanes per screen: Auto and All stack up to 16 lanes in every pace; "4" keeps the 4-lane
// chapter look. Chapters only beyond that.
const lanesMode=settings.lanes||"auto";
const perPage=lanesMode==="4"?4:16;
// Lane geometry per chapter: lane area 544 px under Social's signal band, 654 px otherwise; rows up to 80 px (100 px for ≤4 lanes).
function laneGeometry(n){
 const rowH=Math.max(social?30:26,Math.min(n<=4?100:80,Math.floor((social?544:654)/Math.max(1,n))));
 const bgH=Math.round(rowH*(social?.72:.76)),bgTop=Math.round((rowH-bgH)/2);
 return {rowH,bgH,bgTop,c:bgTop+bgH/2,axisTop:social?144:34,sub:rowH>=40,nameSize:rowH>=46?null:Math.max(14,Math.round(rowH*.44))};
}
const orbitMode=settings.pace==="orbit";
const pages=orbitMode?1:Math.max(1,Math.ceil(D.lanes.length/perPage)), segment=settings.seconds/pages;
const total=settings.seconds+settings.finale;
const anchors=settings.anchors;
function map(value,from,to){
 let lo=0,hi=anchors.length-1;
 while(lo+1<hi){const m=(lo+hi)>>1;if(anchors[m][from]<=value)lo=m;else hi=m;}
 const a=anchors[lo],b=anchors[hi],f=Math.max(0,Math.min(1,(value-a[from])/(b[from]-a[from]||1)));
 return a[to]+(b[to]-a[to])*f;
}
const videoAt=real=>map(real,"real","screen"), realAt=progress=>map(progress,"screen","real");
// Social/Balanced draw the axis in presentation time, so quiet weeks shrink and the
// playhead moves evenly; ticks still print the real clock. Linear keeps real time.
const axisAt=real=>energetic?videoAt(real):Math.max(0,Math.min(1,real/D.span)), realAtAxis=f=>energetic?realAt(f):D.span*f;
const el=(tag,cls,text,parent)=>{let n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);if(parent)parent.appendChild(n);return n;};
// Fit text by measurement instead of CSS ellipsis: the export gate treats overflow
// as clipped text, and system-ui maps to different, wider fonts on Linux hosts.
// Canvas metrics need no layout pass, so this also works inside hidden chapters.
const canvas=document.createElement("canvas"),measurer=canvas.getContext?canvas.getContext("2d"):null;
function fit(n,text,max,min=14){
 text=String(text);
 if(!measurer||typeof getComputedStyle!=="function"){n.textContent=text;return n;}
 const cs=getComputedStyle(n);let size=parseFloat(cs.fontSize)||20;
 const width=(t,s)=>{measurer.font=`${cs.fontStyle} ${cs.fontWeight} ${s}px ${cs.fontFamily}`;return measurer.measureText(t).width;};
 while(size>min&&width(text,size)>max)size-=1;
 let shown=text;if(width(shown,size)>max){while(shown.length>1&&width(shown+"…",size)>max)shown=shown.slice(0,-1);shown+="…";}
 n.style.fontSize=size+"px";n.textContent=shown;if(shown!==text)n.title=text;return n;
}
function motion(n,frames,delay,duration,fill="both",ease="linear"){
 const a=n.animate(frames,{delay:delay*1000,duration:Math.max(0.001,duration)*1000,fill,iterations:1,easing:ease});a.pause();anims.push(a);return a;
}
function show(n,from,until){motion(n,[{opacity:1},{opacity:1}],from,until-from,"none");}
function scene(id,from,length){const n=el("section","scene clip",undefined,root);n.id=id;n.dataset.start=from;n.dataset.duration=length;n.dataset.trackIndex=0;clips.push({n,from,to:from+length});return n;}
function stats(parent,events,full=false,chapter=false){
 const values=full?D.totals:{tools:events.filter(e=>e.kind==="tool").length,errors:events.filter(e=>e.status==="error").length,tokens:events.reduce((s,e)=>s+e.tokens,0),sessions:new Set(events.map(e=>e.profile+e.session)).size,profiles:new Set(events.map(e=>e.profile)).size};
 const row=el("div","stats",undefined,parent);
 const titles=chapter?[["profiles",`Profiles here / ${D.profiles.length}`],["sessions","Sessions here"],["tools","Tool calls here"],["errors","Known errors here"],["tokens","Tokens here"]]:[["profiles","Profiles seen"],["sessions","Agents / sessions"],["tools","Tool calls"],["errors","Known errors"],["tokens","Recorded tokens"]];
 for(const [key,title] of titles){const card=el("div","stat",undefined,row);el("b","",Number(values[key]).toLocaleString("en-US"),card);fit(el("span","",undefined,card),title,290,11);}
}
const fmt=(epoch,options={})=>new Intl.DateTimeFormat("en-US",{timeZone:D.timezone,hour:"2-digit",minute:"2-digit",hourCycle:"h23",...options}).format(new Date(epoch*1000));
function clock(parent,epoch){const c=el("div","clock",fmt(epoch,{month:"short",day:"2-digit"}),parent);el("small","",D.timezone,c);}
const eventCaption=e=>e.caption||({session_start:"Session opened",session_end:"Session ended",turn_start:"Turn started",turn_end:"Turn returned",tool:e.tool||"Tool call",model:"Model step",delegate_start:"Agent delegated",delegate_end:"Agent returned",milestone:"Recorded milestone"}[e.kind])+((e.kind==="tool"&&e.status!=="unknown")||e.status==="error"?" · "+e.status:"");
// Model layer (optional): switches come from recorded model/provider fields only.
const showModels=settings.models!==false;
const providerFor=new Map();for(const e of D.events)if(e.model&&e.provider&&!providerFor.has(e.lane+"|"+e.model))providerFor.set(e.lane+"|"+e.model,e.provider);
const modelText=e=>e.model+(providerFor.get(e.lane+"|"+e.model)?" · "+providerFor.get(e.lane+"|"+e.model):"");
const laneModels=new Map();
for(const lane of D.lanes){
 const mine=D.events.filter(e=>e.lane===lane.id&&e.model);
 // API-call events carry the model that actually answered; prefer them when present.
 const source=mine.some(e=>e.kind==="model")?mine.filter(e=>e.kind==="model"):mine;
 const raw=[];for(const e of source){const r=raw.at(-1);if(r&&r.e.model===e.model){r.end=e.offset;r.sessions.add(e.session);}else raw.push({e,text:modelText(e),end:e.offset,sessions:new Set([e.session])});}
 // A lane groups many sessions, so brief detours (one session on another model, then
 // back) are not shown as switches. A run counts when it spans two or more sessions
 // or at least an hour; neighbouring runs of the same model then merge.
 const runs=[];for(const [k,r] of raw.entries()){if(k&&r.sessions.size<2&&r.end-r.e.offset<3600&&k<raw.length-1)continue;if(runs.length&&runs.at(-1).e.model===r.e.model)continue;runs.push(r);}
 laneModels.set(lane.id,runs);
}
const switches=showModels?[...laneModels.values()].flatMap(r=>r.slice(1).map(x=>({...x.e,caption:`Model → ${x.text}`,switchText:x.text}))):[];
// Representative captions are selected from real event rows, not generated facts.
// Each chapter only narrates its own lanes.
const captionGap=Math.min(social?2:2.5,segment/6)/segment;
function captionsFor(laneIds){
 const evs=D.events.filter(e=>laneIds.has(e.lane));if(!evs.length)return [];
 const keys=[...evs.filter(e=>e.kind==="delegate_start"||e.kind==="delegate_end"||e.status==="error"),...switches.filter(e=>laneIds.has(e.lane))];
 const milestones=[evs[0],...keys,...Array.from({length:10},(_,i)=>evs[Math.round(i*(evs.length-1)/9)]),evs.at(-1)];
 const candidates=[...new Map(milestones.map(e=>[e.id+(e.caption||""),e])).values()].sort((a,b)=>a.time-b.time);
 const picked=candidates.length<=15?candidates:Array.from({length:15},(_,i)=>candidates[Math.round(i*(candidates.length-1)/14)]);
 // A representative ticker may omit adjacent events; it never invents timestamps.
 const spaced=picked.reduce((out,e)=>{if(!out.length||videoAt(e.offset)-videoAt(out.at(-1).offset)>=captionGap)out.push(e);return out;},[]);
 // A caption that would flash by at the chapter's end is dropped rather than cut short.
 return spaced.filter((e,k)=>k===0||(1-videoAt(e.offset))*segment>=1.5);
}
// A readout that swaps text at recorded model changes, coalescing changes closer
// than 0.35 s of video so the stack stays small and readable.
function modelSwap(parent,laneId,initial,offset,max,cls,short=false){
 const box=el("div",cls+" swap",undefined,parent),runs=(laneModels.get(laneId)||[]).map(r=>short?{...r,text:r.e.model}:r);
 const steps=[{t:offset,text:initial}];
 for(const r of runs){const t=offset+segment*videoAt(r.e.offset);if(t-steps.at(-1).t<.35)steps[steps.length-1]={t:Math.max(steps.at(-1).t,offset),text:r.text};else steps.push({t,text:r.text});}
 steps.forEach((x,k)=>{const n=fit(el("div","snapshot",undefined,box),x.text,max,10);show(n,x.t,k+1<steps.length?steps[k+1].t:offset+segment);});
 return box;
}
for(let p=0;p<(orbitMode?0:pages);p++){
 const offset=p*segment, s=scene("timeline-page-"+p,offset,segment);
 const pageLanes=new Set(D.lanes.slice(p*perPage,p*perPage+perPage).map(l=>l.id)),captions=captionsFor(pageLanes);
 // Every pace uses the compact fixed layout; only Social adds the signal band above the lanes.
 s.className+=" social-compact";
 el("div","eyebrow",D.demo?"HERMES / SYNTHETIC DEMO":"HERMES / ACTIVITY REPLAY",s);
 const head=el("div","heading",undefined,s),left=el("div","",undefined,head);
 fit(el("h1","",undefined,left),D.title,1170,36);fit(el("div","chapter",undefined,left),pages>1?`${settings.pace.toUpperCase()} CUT · chapter ${p+1}/${pages} · ${D.lanes.slice(p*perPage,p*perPage+perPage).map(l=>l.profile).filter((x,i,a)=>a.indexOf(x)===i).join(", ")} · counters for this chapter`:`${settings.pace.toUpperCase()} CUT · ${D.profiles.length} profiles`,1170,13);
 if(energetic){motion(left,[{transform:"translateY(20px)",opacity:0},{transform:"translateY(0)",opacity:1}],offset,.5,"both","cubic-bezier(.16,1,.3,1)");}
 const clockStack=el("div","clock-stack",undefined,head), stack=el("div","stat-stack",undefined,s);
 // Discrete metadata readouts are prebuilt. The renderer only seeks paused native
 // animations; no per-frame clocks, callbacks, model calls or network are needed.
 const samples=Math.max(2,Math.ceil(segment*2));
 for(let j=0;j<samples;j++){
   const f=j/(samples-1), t=D.start+realAt(f), a=offset+segment*j/samples,b=offset+segment*(j+1)/samples;
   const snap=el("div","snapshot",undefined,stack);stats(snap,D.events.filter(e=>e.time<=t&&(pages===1||pageLanes.has(e.lane))),false,pages>1);show(snap,a,b);
   if(energetic)motion(snap,[{transform:"scale(1.015)"},{transform:"scale(1)"}],a,.18,"both");
   const cs=el("div","snapshot",undefined,clockStack);clock(cs,t);show(cs,a,b);
 }
 const legend=el("div","legend",undefined,s);
 for(const [color,text] of [["#77c9ff","Tool / activity"],["#ffd074","Delegation / milestone"],["#ff8f91","Known error"],["#9fb6d8","Unknown result ≠ success"],...(showModels&&switches.length?[["#e2c7ff","Model switch"]]:[])]){const l=el("span","",undefined,legend);const i=el("i","",undefined,l);i.style.background=color;l.appendChild(document.createTextNode(text));}
 const plot=el("div","plot",undefined,s), labels=el("div","labels",undefined,plot),axis=el("div","axis",undefined,plot);
 const laneSet=D.lanes.slice(p*perPage,p*perPage+perPage);
 const G=laneGeometry(laneSet.length),rowH=G.rowH;
 labels.style.top=axis.style.top=G.axisTop+"px";axis.style.height=(laneSet.length*rowH)+"px";
 let stage=null,activityReadout=null,cardAt=()=>null;const hubX=740;
 if(social){
   const H=110,hubY=H/2;
   stage=el("div","activity-stage",undefined,plot);el("div","activity-heading","RECORDED EVENT SIGNALS",stage);
   const hub=el("div","activity-hub",undefined,stage);hub.style.left=hubX+"px";el("strong","","H",hub);el("small","","EVENTS",hub);
   activityReadout=el("div","activity-readout",undefined,stage);
   // A tight cluster of four card slots around the hub (not pinned to the frame edges).
   const slots=[[hubX-330,28],[hubX+330,28],[hubX-330,82],[hubX+330,82]];
   for(const [x,y] of slots){const route=el("div","signal-route",undefined,stage),dx=hubX-x,dy=hubY-y;Object.assign(route.style,{left:x+"px",top:y+"px",width:Math.hypot(dx,dy)+"px",transform:`rotate(${Math.atan2(dy,dx)}rad)`});}
   // With more than four lanes the cards show the four most active profiles in each
   // stretch of the replay, keeping a profile in its slot while it stays in the top four.
   const ids=laneSet.map(l=>l.id),spans=[];
   if(ids.length<=4)spans.push({from:offset,to:offset+segment,slots:[0,1,2,3].map(j=>ids[j]??null)});
   else{
     const W=Math.max(2.5,segment/8),total=new Map(ids.map(id=>[id,D.events.filter(e=>e.lane===id).length]));
     let cur=[null,null,null,null];
     for(let a=offset;a<offset+segment-1e-6;a+=W){
       const b=Math.min(offset+segment,a+W),ra=realAt((a-offset)/segment),rb=realAt((b-offset)/segment);
       const count=new Map(ids.map(id=>[id,0]));for(const e of D.events)if(count.has(e.lane)&&e.offset>=ra&&e.offset<=rb)count.set(e.lane,count.get(e.lane)+1);
       const rank=[...ids].sort((x,y)=>(count.get(y)-count.get(x))||((cur.includes(y)?1:0)-(cur.includes(x)?1:0))||(total.get(y)-total.get(x))).slice(0,4);
       const next=cur.map(id=>rank.includes(id)?id:null);for(const id of rank)if(!next.includes(id))next[next.indexOf(null)]=id;
       if(spans.length&&next.every((id,j)=>id===spans.at(-1).slots[j]))spans.at(-1).to=b;else spans.push({from:a,to:b,slots:next});
       cur=next;
     }
   }
   const built=spans.map((sp,k)=>sp.slots.map((id,j)=>{
     if(id==null)return null;const lane=laneSet.find(l=>l.id===id),[x,y]=slots[j],color=palette[D.profiles.indexOf(lane.profile)%palette.length];
     const wrap=el("div","profile-node",undefined,stage);wrap.style.left=x+"px";wrap.style.top=y+"px";wrap.style.color=color;wrap.style.opacity="0";
     const card=el("div","profile-node-inner",undefined,wrap);el("div","profile-node-letter",lane.profile.slice(0,1).toUpperCase(),card);
     const copy=el("div","",undefined,card);fit(el("div","profile-node-name",undefined,copy),lane.profile,175,14);const scope=lane.session==='all'?'ALL RECORDED AGENTS':`AGENT ${lane.session.slice(0,6)}`;
     if(showModels&&(laneModels.get(lane.id)||[]).length)modelSwap(copy,lane.id,scope,offset,175,"profile-node-id");else el("div","profile-node-id",scope,copy);
     const fresh=k===0||spans[k-1].slots[j]!==id;
     show(wrap,sp.from,sp.to);if(fresh)motion(wrap,[{filter:"brightness(1.8)"},{filter:"brightness(1)"}],sp.from,.35,"none","cubic-bezier(.16,1,.3,1)");
     // Packets leave from the card edge facing the hub, never over the card text.
     const dx=hubX-x,dy=hubY-y,reach=Math.hypot(dx,dy)||1,edge=Math.min(1,135/reach);
     return {lane:id,card,x:x+dx*edge,y:y+dy*edge,color};
   }));
   cardAt=(laneId,t)=>{const k=spans.findIndex(sp=>t>=sp.from&&t<sp.to);return k<0?null:(built[k].find(n=>n&&n.lane===laneId)||null);};
 }
 for(let k=0;k<=6;k++){const line=el("div","gridline",undefined,axis);line.dataset.layoutIgnore="";line.style.left=(100*k/6)+"%";const tick=el("span","tick",fmt(D.start+realAtAxis(k/6),D.span>=86400?{month:"short",day:"2-digit",year:D.span>15552000?"numeric":undefined}:{}),axis);tick.style.left=(100*k/6)+"%";
   // End ticks align inward so they stay inside the axis instead of wrapping past its edge.
   if(k===0)tick.style.transform="none";else if(k===6)tick.style.transform="translateX(-100%)";}
 // Night bands are based on real timestamps in the selected timezone. No outage
 // or pause is inferred merely because events are absent.
 if(D.span<=31*86400)for(let k=0;k<96;k++){const f=k/96,ra=realAtAxis(f),rb=realAtAxis((k+1)/96);const hour=Number(fmt(D.start+(ra+rb)/2,{hour:"2-digit",minute:undefined}));if((hour<6||hour>=20)&&rb-ra<=6*3600){const band=el("div","band",undefined,axis);band.dataset.layoutIgnore="";band.style.left=(100*f)+"%";band.style.width=(100/96)+"%";}}
 const fx=el("div","fx-layer",undefined,axis);fx.dataset.layoutIgnore="";
 // Event dots and bars carry no text: one decorative layer, skipped by the layout audit.
 const marks=el("div","marks-layer",undefined,axis);marks.dataset.layoutIgnore="";
 // Keep the per-screen element count near the 4-lane chapter level as lanes stack.
 const bucketsPerLane=Math.max(40,Math.min(160,Math.floor(700/Math.max(1,laneSet.length)))),stackScale=Math.max(1,laneSet.length/4);
 for(let i=0;i<laneSet.length;i++){
   const lane=laneSet[i],color=palette[D.profiles.indexOf(lane.profile)%palette.length];
   const lab=el("div","lane-label",undefined,labels);lab.title=lane.label;lab.style.color=color;lab.style.height=rowH+"px";if(G.nameSize)lab.style.fontSize=G.nameSize+"px";
   fit(el("span","lane-name",undefined,lab),lane.profile,222,12);
   const scopeText=lane.session==="all"?"all agents":`agent ${lane.session.slice(0,6)}`;
   if(G.sub){if(showModels&&(laneModels.get(lane.id)||[]).length)modelSwap(lab,lane.id,scopeText.toUpperCase(),offset,222,"lane-sub",true);else el("span","lane-sub",scopeText,lab);}
   // Recorded model switches: a marker at the switch time on this lane.
   if(showModels)for(const r of (laneModels.get(lane.id)||[]).slice(1)){const at=axisAt(r.e.offset),mk=el("div","model-switch",undefined,axis);mk.style.left=(at*100)+"%";mk.style.top=(i*rowH+Math.max(0,G.bgTop-4))+"px";mk.title=`Model switch → ${r.text}`;
     motion(mk,[{opacity:0,transform:"rotate(45deg) scale(2.2)"},{opacity:1,transform:"rotate(45deg) scale(1)"}],offset+segment*videoAt(r.e.offset),.35,"both","cubic-bezier(.16,1,.3,1)");}
   const bg=el("div","lane-bg",undefined,axis);bg.dataset.layoutIgnore="";bg.style.top=(i*rowH+G.bgTop)+"px";bg.style.height=G.bgH+"px";
   const events=D.events.filter(e=>e.lane===lane.id);
   let lastBurst=-2;
   // Large runs use deterministic time buckets; one dot may stand for several
   // recorded events. Underlying JSON and counters retain every event.
   const buckets=new Map();for(const e of events){const key=events.length>bucketsPerLane?Math.floor(axisAt(e.offset)*bucketsPerLane):e.id;if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(e);}
   for(const bucket of buckets.values()){
     const e=bucket[0], at=axisAt(e.offset), duration=e.duration===null?0:Math.min(e.duration,e.offset);
     const fromReal=Math.max(0,e.offset-duration), from=axisAt(fromReal), n=el("div","mark"+(duration?"":" dot"),undefined,marks);
     n.style.left=(from*100)+"%";n.style.top=(i*rowH+G.c-4.5)+"px";n.style.width=(duration?Math.max(.35,(at-from)*100)+"%":"9px");
     n.style.background=n.style.color=bucket.some(x=>x.status==="error")?"#ff8f91":e.kind.startsWith("delegate")?"#ffd074":color;
     if(duration&&e.kind==="turn_end"){
       n.style.top=(i*rowH+G.bgTop+4)+"px";n.style.height=Math.max(8,G.bgH-8)+"px";n.style.zIndex="1";n.style.background=color+"33";
     }else n.style.zIndex="3";
     n.title=bucket.length>1?`${bucket.length} recorded events in this time bucket`:`${eventCaption(e)} · ${fmt(e.time)}${e.duration===null?" · duration unknown":""}`;
     const appear=offset+segment*videoAt(fromReal), hit=offset+segment*videoAt(e.offset);
     motion(n,[{opacity:0},{opacity:1}],appear,Math.min(.12,segment*(1-from)),"both");
     if(duration){const startReal=fromReal,endReal=e.offset,startScreen=videoAt(startReal),endScreen=videoAt(endReal),w=(at-from)||1;
       const frames=[{transform:"scaleX(0.01)",offset:0},...anchors.filter(a=>a.real>startReal&&a.real<endReal).map(a=>({transform:`scaleX(${Math.max(.01,(axisAt(a.real)-from)/w)})`,offset:(a.screen-startScreen)/(endScreen-startScreen)})),{transform:"scaleX(1)",offset:1}];
       motion(n,frames,appear,Math.max(.03,hit-appear));}
     // Recorded events alone trigger these impacts; gaps stay quiet.
     if(energetic&&hit-lastBurst>(social?.20:.65)*stackScale&&hit<offset+segment-.05){
       lastBurst=hit;const color=n.style.color;
       const flash=el("div","lane-flash",undefined,marks);flash.style.top=(i*rowH+G.bgTop)+"px";flash.style.height=G.bgH+"px";flash.style.background=`linear-gradient(90deg,transparent,${color}55,transparent)`;
       motion(flash,[{opacity:0},{opacity:.8,offset:.15},{opacity:0}],hit,social?.48:.7,"both");
       const ring=el("div","event-ring",undefined,fx);ring.style.left=`calc(${at*100}% - 6px)`;ring.style.top=(i*rowH+G.c-10)+"px";ring.style.color=color;
       motion(ring,[{transform:"scale(.3)",opacity:0},{transform:"scale(.5)",opacity:1,offset:.08},{transform:`scale(${social?Math.min(5,Math.max(2.5,rowH/12)):3})`,opacity:0}],hit,.6,"both","cubic-bezier(.1,.7,.2,1)");
       const count=social?(laneSet.length>4?4:7):3;
       for(let q=0;q<count;q++){
         const spark=el("div","event-spark",undefined,fx),angle=(q*137.5+e.lane*29)*Math.PI/180,dist=26+q*5;
         spark.style.left=(at*100)+"%";spark.style.top=(i*rowH+G.c-2)+"px";spark.style.background=color;
         motion(spark,[{transform:"translate(0,0) scale(1)",opacity:0},{transform:"translate(0,0) scale(1)",opacity:1,offset:.08},{transform:`translate(${Math.cos(angle)*dist}px,${Math.sin(angle)*dist}px) scale(.15)`,opacity:0}],hit,.5,"both","cubic-bezier(.1,.7,.2,1)");
       }
       // A tiny packet flies from a recorded tool event toward its counter.
       if(e.kind==="tool"&&social){const packet=el("div","packet",undefined,s);packet.style.left="0";packet.style.top="0";packet.style.color=packet.style.background=color;
         // Scene coordinates: plot at y=246, lanes from axisTop; target is the tool-call counter.
         const x=341+at*1503,y=246+G.axisTop+i*rowH+G.c;
         packet.dataset.layoutIgnore="";
         motion(packet,[{transform:`translate(${x}px,${y}px)`,opacity:0},{transform:`translate(${x}px,${y}px)`,opacity:1,offset:.08},{transform:`translate(${(x+960)/2}px,${Math.max(232,Math.min(y,300))}px)`,opacity:1,offset:.55},{transform:"translate(960px,216px) scale(.3)",opacity:0}],hit,.65,"both");}
       if(social){
         // Only profiles currently on a card send a signal; the hub pulses for every event.
         const source=cardAt(lane.id,hit);
         if(source){const glow=el("div","node-flash",undefined,source.card);glow.style.background=color;glow.dataset.layoutIgnore="";
           motion(glow,[{opacity:0},{opacity:.26,offset:.15},{opacity:0}],hit,.45,"both");
           const signal=el("div","packet",undefined,stage);signal.dataset.layoutIgnore="";signal.style.left="0";signal.style.top="0";signal.style.background=signal.style.color=color;
           motion(signal,[{transform:`translate(${source.x}px,${source.y}px) scale(.5)`,opacity:0},{transform:`translate(${source.x}px,${source.y}px) scale(1.5)`,opacity:1,offset:.08},{transform:`translate(${hubX}px,55px) scale(2)`,opacity:1,offset:.75},{transform:`translate(${hubX}px,55px) scale(.2)`,opacity:0}],hit,.55,"both");}
         const wave=el("div","hub-wave",undefined,stage);wave.style.color=color;wave.style.left=hubX+"px";wave.dataset.layoutIgnore="";
         motion(wave,[{transform:"scale(.75)",opacity:0},{transform:"scale(1)",opacity:.8,offset:.15},{transform:"scale(1.65)",opacity:0}],hit+.3,.6,"both");
       }
     }
   }
 }
 if(energetic)for(const e of D.events.filter(e=>e.kind==="delegate_start").slice(0,100)){
   const child=laneSet.findIndex(l=>l.id===e.lane),parents=laneSet.map((l,i)=>({l,i})).filter(x=>x.l.session===e.parent);
   if(child<0||parents.length!==1||parents[0].i===child)continue;
   const parent=parents[0].i,top=Math.min(parent,child)*rowH+G.c,height=Math.abs(parent-child)*rowH;
   const link=el("div","",undefined,axis);Object.assign(link.style,{position:"absolute",left:(axisAt(e.offset)*100)+"%",top:top+"px",height:height+"px",width:"2px",background:"#ffd074",transformOrigin:parent<child?"top":"bottom",zIndex:"4"});
   link.title="Recorded agent delegation";motion(link,[{transform:"scaleY(0)",opacity:0},{transform:"scaleY(1)",opacity:.9,offset:.6},{transform:"scaleY(1)",opacity:.3}],offset+segment*videoAt(e.offset),.5,"both");
 }
 const cursor=el("div","playhead",undefined,axis);cursor.style.zIndex="5";motion(cursor,anchors.map(a=>({left:(axisAt(a.real)*100)+"%",offset:a.screen})),offset,segment);
 const ticker=el("div","ticker",undefined,s);el("div","ticker-key","RECORDED MOMENT",ticker);const copy=el("div","ticker-stack",undefined,ticker);
 for(let k=0;k<captions.length;k++){
   const e=captions[k],from=offset+segment*videoAt(e.offset),to=k+1<captions.length?offset+segment*videoAt(captions[k+1].offset):offset+segment;
   if(to<=from)continue;
   const n=fit(el("div","snapshot ticker-copy",undefined,copy),`${e.profile} · ${eventCaption(e)}`,1480,18);show(n,from,to);
   if(energetic)motion(n,[{transform:"translateY(15px) scale(.97)"},{transform:"translateY(0) scale(1)"}],from,Math.min(.24,to-from),"both","cubic-bezier(.16,1,.3,1)");
   if(activityReadout){const readout=fit(el("div","snapshot",undefined,activityReadout),(e.tool?e.tool.replaceAll('_',' ').toUpperCase():eventCaption(e).toUpperCase()),social?550:690,12);show(readout,from,to);motion(readout,[{transform:"translateY(10px) scale(.9)"},{transform:"translateY(0) scale(1)"}],from,.2,"both");}
 }
 const tools=D.events.filter(e=>e.kind==="tool"&&(pages===1||pageLanes.has(e.lane)));
 // Milestone pops share one slot. When thresholds land closer together than one
 // pop's lifetime, keep only the highest one reached, at its own recorded time.
 const POP=1.8,INTRO=(p===0&&energetic)||p>0?1.9:0,pops=[];
 if(energetic)for(const value of [10,25,50,100,250,500,1000,2500,5000,10000,20000]){const e=tools[value-1];if(!e)continue;const t=offset+segment*videoAt(e.offset);if(t>=offset+segment-POP||t<offset+INTRO)continue;
   if(pops.length&&t<pops.at(-1).t+POP)pops[pops.length-1]={value,t};else pops.push({value,t});}
 for(const {value,t} of pops){const pop=el("div","milestone",`${value.toLocaleString()} TOOL CALLS`,s);motion(pop,[{transform:"translateY(-20px) scale(.75)",opacity:0},{transform:"translateY(0) scale(1.06)",opacity:1,offset:.18},{transform:"translateY(0) scale(1)",opacity:1,offset:.8},{transform:"translateY(-10px) scale(.98)",opacity:0}],t,1.8,"both");}
 if(p===0&&energetic){const intro=el("div","intro",undefined,s);intro.dataset.layoutAllowOverlap="true";const copyBox=el("div","intro-copy",undefined,intro),rule=el("div","intro-rule",undefined,copyBox);el("div","eyebrow",D.demo?"SYNTHETIC DEMO":"HERMES ACTIVITY",copyBox);el("div","intro-title",`${D.profiles.length} profiles. In motion.`,copyBox);el("div","intro-detail",`${D.events.length.toLocaleString()} RECORDED EVENTS / ONE REPLAY`,copyBox);
   // Hold an opaque card, clear the words, then dissolve: text never sits over a half-faded dashboard.
   motion(copyBox,[{transform:"scale(1)",opacity:1},{transform:"scale(1.02)",opacity:1,offset:.78},{transform:"scale(1.05)",opacity:0}],offset,1.5,"both");
   motion(intro,[{opacity:1},{opacity:1,offset:.8},{opacity:0}],offset,1.9,"both");motion(rule,[{transform:"scaleX(0)"},{transform:"scaleX(1)"}],offset,.45,"both");}
 if(p>0){const card=el("div","intro",undefined,s);card.dataset.layoutAllowOverlap="true";const box=el("div","intro-copy",undefined,card);el("div","intro-rule",undefined,box);
   el("div","eyebrow",`CHAPTER ${p+1} / ${pages}`,box);
   fit(el("div","intro-title",undefined,box),D.lanes.slice(p*perPage,p*perPage+perPage).map(l=>l.profile).filter((x,i,a)=>a.indexOf(x)===i).join(" · "),1500,40);
   el("div","intro-detail",`REPLAYING ${fmt(D.start,{month:"short",day:"2-digit",hour:undefined,minute:undefined}).toUpperCase()} → ${fmt(D.end,{month:"short",day:"2-digit",hour:undefined,minute:undefined}).toUpperCase()} FOR THESE PROFILES`,box);
   motion(box,[{opacity:1},{opacity:1,offset:.75},{opacity:0}],offset,1.4,"both");motion(card,[{opacity:1},{opacity:1,offset:.78},{opacity:0}],offset,1.8,"both");}
 const foot=el("div","footer",undefined,s);el("span","source-note",energetic?"AXIS COMPRESSES QUIET GAPS / TICKS SHOW THE REAL CLOCK":"LINEAR TIME / OBSERVED METADATA",foot);el("span",D.demo?"demo-tag":"",D.demo?"SYNTHETIC TEST DATA":`${D.events.length.toLocaleString()} recorded events`,foot);
}
// Orbit pace: every recorded event becomes a filament on a tilted, slowly turning ring.
// Profiles own colour sectors; filaments grow when the playhead reaches their real time,
// so the ring fills in as the replay advances. Everything is drawn from time alone
// (seek in the player, hf-seek in exports): no animation loop, no clock, no randomness at draw time.
if(orbitMode){const s=scene("orbit",0,segment);s.className+=" orbit-scene";const W=1920,H=1080,TAU=Math.PI*2;const exportScale=Number((root.dataset||{}).width||0)/1920;const px=exportScale>0?Math.max(.5,Math.min(2,exportScale)):Math.max(1,Math.min(2,window.devicePixelRatio||1));const cv=el("canvas","orbit-canvas",undefined,s);cv.width=Math.round(W*px);cv.height=Math.round(H*px);const g=cv.getContext?cv.getContext("2d"):null;const head=el("div","orbit-head",undefined,s);el("div","orbit-eyebrow","HERMES / ACTIVITY ORBIT",head);fit(el("h1","orbit-title",undefined,head),D.title||"Hermes activity",860,24);fit(el("div","orbit-sub",undefined,head),`${D.profiles.length} profile${D.profiles.length===1?"":"s"} · ${D.totals.events.toLocaleString("en-US")} recorded events · ${D.demo?"synthetic demo data":"metadata only"}`,860,12);const hash=str=>{let h=2166136261;for(const c of String(str)){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return h>>>0;};const rng=seed=>()=>{seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};const upper=(arr,v)=>{let lo=0,hi=arr.length;while(lo<hi){const m=(lo+hi)>>1;if(arr[m]<=v)lo=m+1;else hi=m;}return lo;};const profs=D.profiles.slice(),count=new Map(profs.map(p=>[p,0]));for(const e of D.events)count.set(e.profile,(count.get(e.profile)||0)+1);const floor=.18*Math.sqrt(D.events.length/Math.max(1,profs.length)),weights=profs.map(p=>Math.sqrt(count.get(p)||0)+floor),wsum=weights.reduce((a,b)=>a+b,0)||1;let acc=-Math.PI/2;const sectors=profs.map((p,i)=>{const span=TAU*weights[i]/wsum,hue=((278-i*312/Math.max(1,profs.length-1||1))%360+360)%360,sc={p,start:acc,span,hue,color:`hsl(${hue.toFixed(0)},88%,64%)`};acc+=span;return sc;});const sectorOf=new Map(sectors.map((sc,i)=>[sc.p,i]));const sectorAt=theta=>{let a=((theta+Math.PI/2)%TAU+TAU)%TAU-Math.PI/2;for(let i=0;i<sectors.length;i++)if(a>=sectors[i].start&&a<sectors[i].start+sectors[i].span)return i;return sectors.length-1;};const bornOf=e=>segment*videoAt(e.offset);const ordered=D.events.map(e=>({e,t:bornOf(e)})).sort((a,b)=>a.t-b.t),allBorn=ordered.map(x=>x.t);const cum=key=>{let sum=0;return ordered.map(x=>(sum+=key(x.e)));};const cumTools=cum(e=>e.kind==="tool"?1:0),cumErrors=cum(e=>e.status==="error"?1:0),cumTokens=cum(e=>e.tokens||0);const seen=new Set(),cumSessions=cum(e=>{const k=e.profile+"|"+e.session;if(seen.has(k))return 0;seen.add(k);return 1;});const perProfileBorn=new Map(profs.map(p=>[p,[]]));for(const x of ordered)perProfileBorn.get(x.e.profile)?.push(x.t);const at=(arr,n)=>n>0?arr[n-1]:0;const BINS=160,hist=new Float64Array(BINS),flow=profs.map(()=>new Float64Array(BINS));for(const x of ordered){const b=Math.min(BINS-1,Math.floor(BINS*x.t/Math.max(.001,segment)));hist[b]++;const i=sectorOf.get(x.e.profile);if(i!==undefined)flow[i][b]+=Math.max(1,x.e.tokens||0);}const smooth=(arr,r)=>{const out=new Float64Array(arr.length);for(let b=0;b<arr.length;b++){let s=0,w=0;const R=Math.ceil(r*2);for(let k=-R;k<=R;k++){const j=b+k;if(j<0||j>=arr.length)continue;const q=Math.exp(-k*k/(2*r*r));s+=arr[j]*q;w+=q;}out[b]=s/w;}return out;};for(let i=0;i<flow.length;i++)flow[i]=smooth(flow[i],3.2);const histS=smooth(hist,1.6);hist.set(histS);const histMax=Math.max(1,...hist),flowTot=Array.from({length:BINS},(_,b)=>flow.reduce((s,f)=>s+f[b],0)),flowMax=Math.max(1,...flowTot);const mTotals=new Map();for(const x of ordered)if(x.e.model)mTotals.set(x.e.model,(mTotals.get(x.e.model)||0)+1);const topModels=[...mTotals.entries()].sort((a,b)=>b[1]-a[1]).slice(0,6).map(([m])=>m),modelIdx=new Map(topModels.map((m,i)=>[m,i]));const modelCum=topModels.map(()=>new Float64Array(BINS+1)),otherCum=new Float64Array(BINS+1);for(const x of ordered){if(!x.e.model)continue;const b=Math.min(BINS,1+Math.floor(BINS*x.t/Math.max(.001,segment))),i=modelIdx.get(x.e.model);(i===undefined?otherCum:modelCum[i])[b]++;}for(const arr of [...modelCum,otherCum])for(let b=1;b<=BINS;b++)arr[b]+=arr[b-1];const modelColors=["#e8ecff","#9be7ff","#c3a6ff","#ffcf8a","#9ff0b6","#ff9ec7"];const tokSorted=ordered.map(x=>x.e.tokens||0).filter(v=>v>0).sort((a,b)=>a-b),durSorted=ordered.map(x=>Number(x.e.duration)||0).filter(v=>v>0).sort((a,b)=>a-b),pct=(arr,v)=>arr.length?upper(arr,v)/arr.length:.5;const R0=1,TUBE=.42,THICK=.24,MAX=3600,stride=Math.max(1,Math.ceil(D.events.length/MAX)),strands=[];const lenFor={tool:.58,model:.44,delegate_start:.74,delegate_end:.52,session_start:.3,session_end:.24,turn_start:.32,turn_end:.3,milestone:.62};ordered.forEach((x,k)=>{if(k%stride)return;const e=x.e,si=sectorOf.get(e.profile)??0,sc=sectors[si],r=rng(hash(e.id+":"+k));const tok=e.tokens>0?Math.min(1,Math.log10(1+e.tokens)/6):0;const theta=sc.start+sc.span*(.03+.94*r()),g1=r(),g2=r(),gauss=Math.sqrt(-2*Math.log(g1||1e-9))*Math.cos(TAU*g2),phi=Math.max(-1,Math.min(1,gauss*.45)),elev=Math.max(-.75,Math.min(.75,gauss*.32+(r()-.5)*.25)),inward=false,basis=e.tokens>0?pct(tokSorted,e.tokens):Number(e.duration)>0?.15+.7*pct(durSorted,Number(e.duration)):.42+(r()-.5)*.16,len=.13+.8*basis+(r()-.5)*.05;const R=R0+TUBE*Math.cos(phi),lag=-.12-.1*r(),ct=Math.cos(theta),st0=Math.sin(theta),unit=v=>{const l=Math.hypot(v[0],v[1],v[2])||1;return[v[0]/l,v[1]/l,v[2]/l];},dir=(lagK)=>unit([Math.cos(elev)*ct-lagK*st0,Math.cos(elev)*st0+lagK*ct,Math.sin(elev)]),d=dir(lag),m=dir(lag*.35);strands.push({e,si,born:x.t,theta,len,inward,rx:R*Math.cos(theta),ry:R*Math.sin(theta),rz:THICK*Math.sin(phi),dx:d[0],dy:d[1],dz:d[2],mx:m[0],my:m[1],mz:m[2],err:e.status==="error",lead:e.kind==="tool"||e.kind==="model"||e.kind.startsWith("delegate")||e.status==="error"});});const strandBorn=strands.map(x=>x.born);const belt=[],br=rng(hash((D.title||"")+"|belt|"+D.events.length));for(let i=0;i<22000;i++){const theta=br()*TAU,ph=br()*TAU,u=Math.sqrt(br()),R=R0+TUBE*u*Math.cos(ph);belt.push({x:R*Math.cos(theta),y:R*Math.sin(theta),z:THICK*u*Math.sin(ph),si:sectorAt(theta),vivid:br()<.7,tone:Math.floor(br()*3),size:br()<.1?2.4:br()<.5?1.7:1.3});}const pose=t=>({yaw:-(.62+.15*Math.sin(.33*t)),pitch:.2+.11*Math.sin(.26*t+1),roll:.07*Math.sin(.21*t+.5),spin:.3*t});const CX=700,CY=532,SC=184,F=3.4;let P,cy,sy,cp,sp,ca,sa,cr,sr;const setPose=t=>{P=pose(t);cy=Math.cos(P.yaw);sy=Math.sin(P.yaw);cp=Math.cos(P.pitch);sp=Math.sin(P.pitch);ca=Math.cos(P.spin);sa=Math.sin(P.spin);cr=Math.cos(P.roll);sr=Math.sin(P.roll);};const proj3=(x,y,z,out)=>{const xr=x*ca-y*sa,yr=x*sa+y*ca,x1=xr*cy+z*sy,z1=-xr*sy+z*cy,y2=yr*cp-z1*sp,z2=yr*sp+z1*cp,k=F/(F+z2),u=SC*k*x1,v=SC*k*y2;out[0]=CX+u*cr-v*sr;out[1]=CY+u*sr+v*cr;out[2]=z2;out[3]=k;return out;};const proj=(r,theta,z,out)=>proj3(r*Math.cos(theta),r*Math.sin(theta),z,out);const p0=[0,0,0,1],p1=[0,0,0,1],p2=[0,0,0,1];const mono='ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace';const txt=(text,x,y,size,color,weight=500,align="left")=>{g.font=`${weight} ${size}px ${mono}`;g.fillStyle=color;g.textAlign=align;g.fillText(String(text),x,y);};const short=n=>n>=1e9?(n/1e9).toFixed(2)+"B":n>=1e6?(n/1e6).toFixed(1)+"M":n>=1e4?(n/1e3).toFixed(1)+"k":Math.round(n).toLocaleString("en-US");function drawOrbit(time){if(!g)return;const T=Math.max(0,Math.min(segment,time));setPose(T);g.setTransform(px,0,0,px,0,0);g.globalAlpha=1;g.clearRect(0,0,W,H);const n=upper(strandBorn,T),N=upper(allBorn,T);const lit=sectors.map(sc=>{const arr=perProfileBorn.get(sc.p)||[];return arr.length?upper(arr,T)/arr.length:0;});const recent=N-upper(allBorn,T-1.5),rate=recent/Math.max(1,D.events.length/Math.max(1,segment)*1.5);const scanA=.66*T,scanStrength=.35+.65*Math.min(1,rate);const scanOf=theta=>{let d=((theta+P.spin-scanA)%TAU+TAU)%TAU;if(d>Math.PI)d-=TAU;return Math.exp(-d*d/(2*.16*.16));};const drawBelt=()=>{const groups=new Map();for(const f of belt){proj3(f.x,f.y,f.z,p0);const depth=p0[2]>.15?0:p0[2]<-.15?2:1;let key,fill;if(f.vivid){const lv=Math.round(lit[f.si]*4)/4,a=(.3+.6*lv)*(.5+.25*depth),h=(sectors[f.si].hue+(f.tone-1)*14+360)%360;key="v"+f.si+"|"+depth+"|"+f.tone+"|"+lv;fill=`hsla(${h.toFixed(0)},${70+10*f.tone}%,${58+8*f.tone}%,${a.toFixed(2)})`;}else{key="s"+depth;fill=`rgba(128,142,182,${(.2+.12*depth).toFixed(2)})`;}let grp=groups.get(key);if(!grp){grp={fill,pts:[]};groups.set(key,grp);}grp.pts.push(p0[0],p0[1],f.size);}for(const grp of groups.values()){g.fillStyle=grp.fill;g.beginPath();for(let i=0;i<grp.pts.length;i+=3)g.rect(grp.pts[i],grp.pts[i+1],grp.pts[i+2],grp.pts[i+2]);g.fill();}};const lines=new Map(),tips=new Map();const add=(map,key,style)=>{let v=map.get(key);if(!v){v={style,list:[]};map.set(key,v);}return v.list;};for(let i=0;i<n;i++){const st=strands[i],age=T-st.born,grow=Math.min(1,age/.55),ease=1-Math.pow(1-grow,3),sc=sectors[st.si];const fresh=Math.max(0,1-age/1.4),scan=scanOf(st.theta)*scanStrength,settle=1+.22*Math.exp(-Math.max(0,age-.5)/.7)*Math.min(1,age/.5),L=st.len*ease*settle;proj3(st.rx,st.ry,st.rz,p0);proj3(st.rx+st.mx*L*.5,st.ry+st.my*L*.5,st.rz+st.mz*L*.5,p1);proj3(st.rx+st.dx*L,st.ry+st.dy*L,st.rz+st.dz*L,p2);const level=fresh>.35?2:scan>.3?1:0,dz=p2[2]>.3?0:p2[2]<-.3?2:1,lineA=Math.min(1,[.14,.42,.8][level]*[.6,.9,1.2][dz]);add(lines,st.si+"|"+level+"|"+dz,`hsla(${sc.hue.toFixed(0)},80%,${level?72:62}%,${lineA.toFixed(2)})`).push(p0[0],p0[1],p1[0],p1[1],p2[0],p2[1]);const tipKey=st.err?"err":st.si+"|"+(level?1:0);add(tips,tipKey,st.err?"rgba(255,92,108,.95)":`hsla(${sc.hue.toFixed(0)},92%,${level?82:70}%,${level?.98:.78})`).push(p2[0],p2[1],(level===2?3.4:st.err?2.4:1.6)*Math.min(1.5,Math.max(.6,p2[3])));}const strokeLines=far=>{g.lineWidth=.9;for(const [key,v] of lines){if(key.endsWith("|0")!==far)continue;g.strokeStyle=v.style;g.beginPath();const L=v.list;for(let i=0;i<L.length;i+=6){g.moveTo(L[i],L[i+1]);g.quadraticCurveTo(L[i+2],L[i+3],L[i+4],L[i+5]);}g.stroke();}};strokeLines(true);drawBelt();strokeLines(false);for(const v of tips.values()){g.fillStyle=v.style;g.beginPath();const L=v.list;for(let i=0;i<L.length;i+=3){g.moveTo(L[i]+L[i+2],L[i+1]);g.arc(L[i],L[i+1],L[i+2],0,TAU);}g.fill();}g.save();g.globalCompositeOperation="lighter";for(let k=-6;k<=6;k++){const th=scanA-P.spin+k*.035;proj(.95,th,0,p0);proj(2.05,th,0,p1);g.strokeStyle=`rgba(235,240,255,${(.11*scanStrength*Math.exp(-k*k/14)).toFixed(3)})`;g.lineWidth=1.3;g.beginPath();g.moveTo(p0[0],p0[1]);g.lineTo(p1[0],p1[1]);g.stroke();}g.restore();const q=Math.floor(T/1.2)*1.2;let li=upper(strandBorn,q)-1;while(li>=0&&!strands[li].lead)li--;if(li>=0){const st=strands[li],age=T-st.born,ease=1-Math.pow(1-Math.min(1,age/.55),3);const LL=st.len*ease*(1+.22*Math.exp(-Math.max(0,age-.5)/.7)*Math.min(1,age/.5));proj3(st.rx+st.dx*LL,st.ry+st.dy*LL,st.rz+st.dz*LL,p2);const bx=1010,by=150,bw=300,bh=82,sc=sectors[st.si];g.strokeStyle="rgba(255,255,255,.9)";g.lineWidth=1.4;g.beginPath();g.arc(p2[0],p2[1],9,0,TAU);g.stroke();g.strokeStyle="rgba(255,110,110,.75)";g.lineWidth=1;g.beginPath();g.moveTo(p2[0],p2[1]);g.lineTo(bx,by+bh/2);g.stroke();g.fillStyle="rgba(8,9,16,.92)";g.fillRect(bx,by,bw,bh);g.strokeStyle="rgba(255,96,96,.85)";g.strokeRect(bx+.5,by+.5,bw-1,bh-1);const e=st.e,clip=(t,m)=>{t=String(t);return t.length>m?t.slice(0,m-1)+"…":t;};txt(clip(`${e.profile} · ${e.kind==="tool"?"TOOL":e.kind.startsWith("delegate")?"DELEGATE":e.status==="error"?"ERROR":"MODEL"}`.toUpperCase(),30),bx+14,by+24,13,"#ff7a7a",600);txt(clip(eventCaption(e),30),bx+14,by+49,16,"#f2f4ff",600);txt(clip([e.model,e.status!=="unknown"?e.status:"",fmt(D.start+e.offset,{month:"short",day:"2-digit"})].filter(Boolean).join(" · "),36),bx+14,by+70,12,"#9aa3c4");g.fillStyle=sc.color;g.fillRect(bx,by,3,bh);}const progress=T/Math.max(.001,segment),real=realAt(Math.min(1,progress));txt(fmt(D.start+real,{month:"short",day:"2-digit"}),1858,62,26,"#f2f4ff",600,"right");txt(D.timezone,1858,86,12,"#8d96b8",500,"right");const stats=[["TOOL CALLS",at(cumTools,N)],["SESSIONS",at(cumSessions,N)],["TOKENS",at(cumTokens,N)],["ERRORS",at(cumErrors,N)]];stats.forEach(([label,v],k)=>{const x=1330+k*132;txt(short(v),x,150,24,k===3&&v?"#ff7a85":"#f2f4ff",650);txt(label,x,172,11,"#8d96b8",500);});const listTop=222,rowH=Math.max(22,Math.min(34,Math.floor(430/Math.max(1,sectors.length))));txt("PROFILES · LIVE EVENTS",1330,listTop-12,12,"#8d96b8",600);const maxCount=Math.max(1,...profs.map(p=>count.get(p)||0));sectors.forEach((sc,k)=>{if(listTop+k*rowH>660)return;const y=listTop+k*rowH,arr=perProfileBorn.get(sc.p)||[],c=upper(arr,T);g.fillStyle=sc.color;g.fillRect(1330,y+6,10,10);txt((sc.p.length>18?sc.p.slice(0,17)+"…":sc.p),1350,y+16,14,"#e8ebfa",500);g.fillStyle="rgba(255,255,255,.07)";g.fillRect(1540,y+6,220,9);g.fillStyle=sc.color;g.globalAlpha=.85;g.fillRect(1540,y+6,220*c/maxCount,9);g.globalAlpha=1;txt(short(c),1858,y+16,13,"#c9cfe8",500,"right");});const shown=sectors.filter((_,k)=>listTop+k*rowH<=660).length,sy0=listTop+shown*rowH+52,sh=80,sx=1330,sw=528;txt("ACTIVITY · EVENTS PER BIN",sx,sy0-14,12,"#8d96b8",600);g.strokeStyle="rgba(255,255,255,.08)";g.strokeRect(sx+.5,sy0+.5,sw,sh);const cut=Math.min(BINS,Math.ceil(BINS*progress));for(const [limit,style] of [[BINS,"rgba(141,150,184,.25)"],[cut,"#9be7ff"]]){g.strokeStyle=style;g.lineWidth=1.4;g.beginPath();for(let b=0;b<limit;b++){const x=sx+sw*(b+.5)/BINS,y=sy0+sh-6-(sh-12)*hist[b]/histMax;b?g.lineTo(x,y):g.moveTo(x,y);}g.stroke();}if(showModels&&topModels.length){const my=sy0+sh+58,mb=Math.min(BINS,Math.ceil(BINS*progress)),vals=[...topModels.map((m,i)=>[m,modelCum[i][mb],modelColors[i]]),["other",otherCum[mb],"#5d6585"]].filter(v=>v[1]>0),sum=vals.reduce((a,v)=>a+v[1],0);txt("MODELS · SHARE OF RECORDED EVENTS",sx,my-14,12,"#8d96b8",600);g.fillStyle="rgba(255,255,255,.07)";g.fillRect(sx,my,sw,12);let mx=sx;for(const [,c,color] of vals){const w=sw*c/(sum||1);g.fillStyle=color;g.fillRect(mx,my,Math.max(0,w-1),12);mx+=w;}vals.slice(0,5).forEach(([m,c,color],k)=>{const y=my+36+k*24;g.fillStyle=color;g.fillRect(sx,y-9,9,9);txt(m.length>34?m.slice(0,33)+"…":m,sx+18,y,13,"#d9ddf0",500);txt(`${Math.round(100*c/(sum||1))}%`,sx+sw,y,13,"#c9cfe8",500,"right");});}const fx=64,fw=1792,fy=966,fh=74;txt("TOKEN FLOW BY PROFILE",fx,fy-14,12,"#8d96b8",600);txt(`${short(at(cumTokens,N))} TOKENS`,fx+fw,fy-14,12,"#c9cfe8",600,"right");const base=new Float64Array(BINS);for(let i=0;i<sectors.length;i++){g.fillStyle=sectors[i].color;g.globalAlpha=.78;g.beginPath();for(let b=0;b<cut;b++){const x=fx+fw*b/(BINS-1),y=fy+fh-fh*(base[b]+flow[i][b])/flowMax;b?g.lineTo(x,y):g.moveTo(x,y);}for(let b=cut-1;b>=0;b--){const x=fx+fw*b/(BINS-1),y=fy+fh-fh*base[b]/flowMax;g.lineTo(x,y);}if(cut>1)g.fill();for(let b=0;b<cut;b++)base[b]+=flow[i][b];}g.globalAlpha=1;g.strokeStyle="rgba(255,255,255,.55)";g.lineWidth=1;const hx=fx+fw*Math.min(1,progress);g.beginPath();g.moveTo(hx,fy-4);g.lineTo(hx,fy+fh);g.stroke();txt(`ORBIT · ${(scanA*180/Math.PI%360).toFixed(0)}° SCAN · ${short(N)} / ${short(D.events.length)} EVENTS${stride>1?` · 1 FILAMENT = ${stride} EVENTS`:""} · RAY LENGTH = TOKENS, ELSE DURATION, ELSE AVERAGE`,64,930,12,"#6f7896",500);}drawers.push(drawOrbit);}
const close=scene("timeline-finale",settings.seconds,settings.finale),inner=el("div","closing",undefined,close);inner.style.height="100%";
inner.dataset.hold="true";
el("div","eyebrow",D.demo?"SYNTHETIC DEMO / FINAL TOTALS":"REPLAY COMPLETE / RECORDED TOTALS",inner);
const finalTitle=el("h1","",`${D.totals.tools.toLocaleString()} tool calls.`,inner);stats(inner,D.events,true);
if(energetic){motion(finalTitle,[{transform:"translateY(35px) scale(.9)",opacity:0},{transform:"translateY(0) scale(1)",opacity:1}],settings.seconds,.45,"both","cubic-bezier(.16,1,.3,1)");}
el("div","closing-date",`${fmt(D.start,{month:"short",day:"2-digit"})} → ${fmt(D.end,{month:"short",day:"2-digit"})} · ${(D.span/3600).toFixed(2)} elapsed hours`,inner);
if(showModels){
 // Usage share by recorded model events (API calls when present, else session records).
 // Usage share by session: each (profile, session, model) counts once, whether it came
 // from live API-call capture or saved session history, so profiles are comparable.
 const tally=(key)=>{const seen=new Set(),m=new Map();for(const e of D.events){const v=e[key];if(!v)continue;const k=e.profile+"|"+e.session+"|"+v;if(seen.has(k))continue;seen.add(k);m.set(v,(m.get(v)||0)+1);}return [...m.entries()].sort((a,b)=>b[1]-a[1]);};
 const ms=tally("model"),ps=tally("provider"),n=ms.reduce((s,[,c])=>s+c,0)||1;
 const line=(list,top,fmtItem)=>list.slice(0,top).map(fmtItem).join(" · ")+(list.length>top?` · +${list.length-top} more`:"");
 if(ms.length)fit(el("div","closing-models",undefined,inner),`MODELS BY SESSION: ${line(ms,4,([m,c])=>`${m} ${Math.max(1,Math.round(100*c/n))}%`)}`,1700,15);
 if(ps.length)fit(el("div","closing-models",undefined,inner),`PROVIDERS: ${line(ps,5,([p])=>p)}`,1700,15);}
el("div","closing-note",`${D.totals.events.toLocaleString()} observed events · ${D.totals.profiles} profiles · ${D.totals.unknown_status.toLocaleString()} outcomes not recorded`,inner);
const foot=el("div","footer",undefined,close);el("span","",D.demo?"DEMO — NOT REAL AGENT ACTIVITY":"Private local artifact · no transcript content",foot);el("span","","HERMES / TIMELINE REPLAY",foot);
// Standalone playback driver only. Export compositions omit the driver entirely;
// HyperFrames owns animation time and clip visibility in index.html.
function seek(t){t=Math.max(0,Math.min(total,t));for(const a of anims)a.currentTime=t*1000;for(const f of drawers)f(t);for(const c of clips)c.n.style.visibility=t>=c.from&&(t<c.to||t===total&&c.to===total)?"visible":"hidden";return t;}
window.TimelineReplay={seek,duration:total,data:D,animations:anims,chapters:pages,pacing:settings.pace,videoAt,realAt};
// Exports: HyperFrames seeks with hf-seek; canvas layers redraw from that time alone.
if(!settings.interactive&&drawers.length&&typeof window.addEventListener==="function"){window.addEventListener("hf-seek",e=>{for(const f of drawers)f(e.detail.time);});for(const f of drawers)f(0);}
if(settings.interactive){
 const shell=document.querySelector(".viewport"), play=document.getElementById("play"),scrub=document.getElementById("scrub"),speed=document.getElementById("speed"),out=document.getElementById("position");
 let t=0,running=false,last=null,raf=0,loop=Boolean(settings.loop);
 const loopButton=document.getElementById("loop");
 // Play once by default; the host page (Desktop) remembers the choice and tells us.
 const setLoop=(value,announce)=>{loop=Boolean(value);loopButton.setAttribute("aria-pressed",String(loop));loopButton.textContent=loop?"Loop: on":"Loop: off";if(announce&&parent!==window)parent.postMessage({type:"timeline-replay:loop-changed",loop},"*");};
 loopButton.onclick=()=>{setLoop(!loop,true);if(loop&&!running&&t>=total){t=0;start();}};
 window.addEventListener("message",ev=>{if(ev.source===parent&&ev.data&&ev.data.type==="timeline-replay:loop")setLoop(ev.data.loop,false);});
 setLoop(loop,false);
 const resize=()=>root.style.transform=`scale(${shell.clientWidth/1920})`;new ResizeObserver(resize).observe(shell);resize();
 const paint=()=>{seek(t);scrub.value=t;out.textContent=`${t.toFixed(1)} / ${total.toFixed(1)} s`;play.textContent=running?"Pause":(t>=total?"Replay":"Play");};
 function frame(now){if(!running)return;const dt=last===null?0:(now-last)/1000;last=now;t=Math.min(total,t+dt*Number(speed.value));if(t>=total){if(loop){t=0;last=null;}else running=false;}paint();if(running)raf=requestAnimationFrame(frame);}
 function start(){running=true;last=null;cancelAnimationFrame(raf);raf=requestAnimationFrame(frame);paint();}
 play.onclick=()=>{if(running){running=false;cancelAnimationFrame(raf);paint();}else{if(t>=total)t=0;start();}};
 document.getElementById("restart").onclick=()=>{t=0;paint();};scrub.max=total;scrub.oninput=()=>{t=Number(scrub.value);paint();};
 document.getElementById("end").onclick=()=>{running=false;cancelAnimationFrame(raf);t=total;paint();};
 if(matchMedia("(prefers-reduced-motion: reduce)").matches){t=total;paint();}else{paint();start();}
 const notes=document.getElementById("notes");for(const w of D.warnings)el("li","",w,notes);
}
})();
'''


RESOLUTIONS = {"720p": (1280, 720), "1080p": (1920, 1080), "1440p": (2560, 1440), "2160p": (3840, 2160)}


def html(model, seconds=60, interactive=True, pace="social", models=True, lanes="auto", resolution="1080p"):
    total = max(10, min(180, number(seconds, 60)))
    body, finale = presentation.split(total, pace)
    width, height = RESOLUTIONS.get(resolution, RESOLUTIONS["1080p"])
    settings = dict(seconds=body, finale=finale, interactive=interactive, pace=pace, models=bool(models), lanes=lanes if lanes in ("auto", "4", "all") else "auto", loop=False, anchors=presentation.anchors(model,pace))
    duration = total
    # Script-safe JSON prevents inline HTML/script injection, even in imported data.
    def slim(data):
        if not isinstance(data, dict) or "events" not in data:
            return data
        keep = dict(data)
        keep["events"] = [{k: (v[:12] if k == "id" else v) for k, v in e.items() if k != "origin"} for e in data["events"]]
        return keep

    def encoded(data):
        return json.dumps(slim(data), ensure_ascii=True, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    width, height = RESOLUTIONS.get(resolution, RESOLUTIONS["1080p"])
    root = f'<div id="root" data-composition-id="timeline-replay" data-width="{width}" data-height="{height}" data-start="0" data-duration="{duration:g}" data-fps="30" data-no-timeline="true"></div>'
    if interactive:
        root = '<div id="root"></div>'
        root = '<main class="artifact-shell"><div class="viewport">'+root+'</div><nav class="controls" aria-label="Replay controls"><button id="play">Play</button><button id="restart">Restart</button><button id="end">Final totals</button><button id="loop" aria-pressed="false" title="Loop playback">Loop: off</button><label>Speed <select id="speed"><option>0.5</option><option selected>1</option><option>2</option><option>4</option></select></label><input id="scrub" aria-label="Replay position" type="range" min="0" step="0.05" value="0"><output id="position"></output></nav><details class="details"><summary>Data provenance and coverage notes</summary><ul id="notes"></ul><p>Only recorded metadata is visualized. Unknown outcomes are not successes. Video rendering is an explicit action on the Hermes host.</p></details></main>'
    script = JS if interactive else JS.split('if(settings.interactive){', 1)[0]+'})();'
    # Native output size: HyperFrames sizes the capture frame from data-width/height, so the root is the
    # real size and each scene (laid out at 1920x1080) zooms to it. Zoom on descendants is honoured;
    # zoom on the root is not. This keeps the BeginFrame path; --resolution would supersample via screenshot.
    css = CSS
    if not interactive and width != 1920:
        css += "#root>.scene{width:1920px;height:1080px;right:auto;bottom:auto;zoom:%.6f}" % (width / 1920)
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hermes Timeline Replay</title><style>'+css+'</style></head><body>'+root+'<script type="application/json" id="replay-data">'+encoded(model)+'</script><script type="application/json" id="replay-settings">'+encoded(settings)+'</script><script>'+script+'</script></body></html>'


def bundle(model, seconds=60, home=None, pace="social", models=True, lanes="auto", resolution="1080p", meta=None):
    identifier = secrets.token_hex(8)
    folder = data_dir(home) / "renders" / identifier
    folder.mkdir(parents=True, exist_ok=False)
    seconds = max(10, min(180, number(seconds, 60)))
    duration = seconds  # the requested length is the whole video, finale included
    (folder / "replay.html").write_text(html(model, seconds, True, pace, models, lanes), encoding="utf-8")
    (folder / "index.html").write_text(html(model, seconds, False, pace, models, lanes, resolution), encoding="utf-8")
    (folder / "events.json").write_text(json.dumps(model, indent=2), encoding="utf-8")
    from .version import VERSION, API
    per_screen = 4 if lanes == "4" else 16
    screen_lanes = min(len(model["lanes"]), per_screen)
    width, height = RESOLUTIONS.get(resolution, RESOLUTIONS["1080p"])
    meta = dict(meta or {})
    profiles = len(model["profiles"])
    # A human title for Exports, e.g. "Hermes activity · Last 7 days · Social · 34 s · 7 profiles".
    title_bits = [model.get("title") or "Hermes activity", meta.get("range_label") or ("Synthetic demo" if model["demo"] else "Selected range"),
                  pace.capitalize(), f"{duration:g} s", f"{profiles} profile{'s' if profiles != 1 else ''}"]
    if resolution != "1080p":
        title_bits.append(resolution)
    (folder / "bundle.json").write_text(json.dumps(dict(id=identifier, version=VERSION, api=API, screen_lanes=screen_lanes, title=" · ".join(title_bits),
        created=time.time(), resolution=resolution, width=width, height=height, range_label=meta.get("range_label"), duration=duration, pace=pace, models=bool(models), lanes=lanes, demo=model["demo"], totals=model["totals"])), encoding="utf-8")
    (folder / "package.json").write_text(json.dumps({"private": True, "scripts": {"check": "hyperframes check .", "render": "hyperframes render . --output timeline.mp4 --fps 30 --quality looks --workers 1"}}, indent=2), encoding="utf-8")
    return dict(ok=True, bundle=identifier, title=" · ".join(title_bits), resolution=resolution, html=str(folder / "replay.html"), composition=str(folder / "index.html"), duration=duration, pace=pace, models=bool(models), lanes=lanes, totals=model["totals"], demo=model["demo"], warnings=model["warnings"])
