// Usage: node render_map.js monatsupdate.html map.png  – screenshot of the map (for the PowerPoint deck)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [inp, out] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2.5 });
  await page.goto('file://' + path.resolve(inp));
  await page.evaluate(() => document.fonts.ready);
  await page.locator('svg[aria-label^="Karte"]').screenshot({ path: out, omitBackground: true });
  await browser.close();
})();
