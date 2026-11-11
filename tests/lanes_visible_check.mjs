// Optional real-browser check: every lane label and lane row sits inside its plot and the
// 1920x1080 frame, at every chapter. Uses an installed puppeteer-core + Chromium; no downloads.
// Usage: node tests/lanes_visible_check.mjs PUPPETEER_CORE_ENTRY CHROME index.html [more.html ...]
import {pathToFileURL} from 'node:url';
const [pptr, chrome, ...files] = process.argv.slice(2);
if (!pptr || !chrome || !files.length) throw new Error('Pass puppeteer-core entry, Chromium path and composition files');
const puppeteer = (await import(pathToFileURL(pptr).href)).default;
const browser = await puppeteer.launch({executablePath: chrome, headless: true, args: ['--disable-gpu']});
let failed = 0;
try {
  for (const file of files) {
    const page = await browser.newPage();
    await page.setViewport({width: 1920, height: 1080});
    await page.goto(pathToFileURL(file).href);
    const result = await page.evaluate(() => {
      // HyperFrames sizes the root from data-width/height at render time; do the same here.
      const root = document.getElementById('root');root.style.width = '1920px';root.style.height = '1080px';
      const problems = [];let lanes = 0;
      for (const scene of document.querySelectorAll('section.scene[id^="timeline-page-"]')) {
        scene.style.visibility = 'visible';
        const plot = scene.querySelector('.plot').getBoundingClientRect(), frame = scene.getBoundingClientRect();
        const rows = [...scene.querySelectorAll('.lane-label'), ...scene.querySelectorAll('.lane-bg')];
        for (const el of rows) {
          const r = el.getBoundingClientRect();lanes += el.classList.contains('lane-label') ? 1 : 0;
          if (r.height < 8 || r.top < plot.top - 1 || r.bottom > plot.bottom + 1 || r.bottom > frame.bottom - 120)
            problems.push(`${scene.id} ${el.className} "${el.textContent.slice(0, 30)}" top ${Math.round(r.top)} bottom ${Math.round(r.bottom)} (plot ${Math.round(plot.top)}–${Math.round(plot.bottom)})`);
        }
      }
      return {lanes, expected: JSON.parse(document.getElementById('replay-data').textContent).lanes.length, problems};
    });
    const ok = !result.problems.length && result.lanes === result.expected;
    if (!ok) failed++;
    console.log(JSON.stringify({file: file.split(/[\\/]/).slice(-2).join('/'), ok, lanes: result.lanes, expected: result.expected, problems: result.problems.slice(0, 5)}));
    await page.close();
  }
} finally { await browser.close(); }
if (failed) process.exit(1);
