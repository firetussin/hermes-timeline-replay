// Optional real-browser check using an already-installed Playwright and Chromium.
// Does not download software, start a web server, or encode a video.
import {pathToFileURL} from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const [modulePath,browserPath]=process.argv.slice(2);
if(!modulePath||!browserPath)throw new Error('Pass installed playwright-core module and Chromium executable paths');
const {chromium}=await import(pathToFileURL(modulePath).href);
const browser=await chromium.launch({executablePath:browserPath,headless:true,args:['--disable-gpu']});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url());});
 await page.goto(pathToFileURL(path.resolve('demo/replay.html')).href);
 await page.waitForFunction(()=>Boolean(window.TimelineReplay));
 if(await page.locator('#play').textContent()==='Pause')await page.locator('#play').click();
 await page.locator('#scrub').fill('15');await page.locator('#scrub').dispatchEvent('input');
 assert.match(await page.locator('#position').textContent(),/^15\.0/);
 assert.equal(await page.locator('#timeline-page-0').evaluate(n=>getComputedStyle(n).visibility),'visible');
 await page.locator('#end').click();
 assert.equal(await page.locator('#timeline-finale').evaluate(n=>getComputedStyle(n).visibility),'visible');
 await page.locator('#restart').click();
 assert.equal(await page.locator('#timeline-page-0').evaluate(n=>getComputedStyle(n).visibility),'visible');
 const before=await page.evaluate(()=>{window.TimelineReplay.seek(22);return document.getAnimations().map(a=>a.currentTime);});
 const after=await page.evaluate(()=>{window.TimelineReplay.seek(window.TimelineReplay.duration);window.TimelineReplay.seek(0);window.TimelineReplay.seek(22);return document.getAnimations().map(a=>a.currentTime);});
 assert.deepEqual(after,before);
 await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:390,height:844});await page.reload();
 assert.equal(await page.locator('#timeline-finale').evaluate(n=>getComputedStyle(n).visibility),'visible');
 assert.equal(await page.locator('#play').textContent(),'Play');
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+1);
 assert.equal(overflow,false);
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);
 console.log('Browser: interactive controls, reverse seeks, reduced-motion finale, phone-width fit, no page errors or network passed.');
}finally{await browser.close();}
