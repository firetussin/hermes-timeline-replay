// Visual/fit check of the generated mocked-SDK design fixture, not the live app.
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const {chromium}=await import(pathToFileURL(process.argv[2]).href);
const browser=await chromium.launch({executablePath:process.argv[3],headless:true,args:['--disable-gpu']});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1180}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.resolve('demo/desktop-preview.html')).href);
 const frame=page.frames().find(f=>f!==page.mainFrame());
 await frame.waitForFunction(()=>Boolean(window.TimelineReplay));
 if(await frame.locator('#play').textContent()==='Pause')await frame.locator('#play').click();
 await frame.locator('#scrub').fill('8');await frame.locator('#scrub').dispatchEvent('input');
 await page.screenshot({path:'demo/desktop-dark.png',fullPage:true});
 const dark=await page.locator('.tr-page').evaluate(n=>getComputedStyle(n).color);
 await page.getByRole('button',{name:'Light',exact:true}).click();
 const light=await page.locator('.tr-page').evaluate(n=>getComputedStyle(n).color);
 assert.notEqual(dark,light);
 await page.screenshot({path:'demo/desktop-light.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
 assert.deepEqual(errors,[]);
 console.log('Desktop design fixture: dark/light theme variables, responsive width, sample playback and no browser errors passed.');
}finally{await browser.close();}
