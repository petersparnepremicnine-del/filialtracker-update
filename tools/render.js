// Usage: node render.js in.html out.png [out.pdf]
// PNG (screen): one page, A4 portrait proportions, 1.5x.
// PDF (print): A4 landscape, 2 pages (page break before the renovation section), readable font sizes.
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [inp, png, pdf] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1.5 });
  await page.goto('file://' + path.resolve(inp));
  await page.evaluate(() => document.fonts.ready);
  const minH = Math.ceil(1600 * 1123 / 794);
  await page.evaluate((h) => { document.body.style.minHeight = h + 'px'; }, minH);
  const h = await page.evaluate(() => document.body.scrollHeight);
  if (h > minH) console.error(`Hinweis: PNG ist höher als A4-Proportion (${h}px > ${minH}px)`);
  await page.screenshot({ path: png, fullPage: true });
  if (pdf) {
    await page.evaluate(() => { document.body.style.minHeight = ''; });
    // shrink a little if a busy month would spill onto a third page
    let scale = 1123 / 1600, pages = 99;
    for (let i = 0; i < 6 && pages > 2; i++) {
      const buf = await page.pdf({ format: 'A4', landscape: true, printBackground: true,
                                   scale, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
      pages = (buf.toString('latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;
      if (pages <= 2) { require('fs').writeFileSync(pdf, buf); break; }
      scale *= 0.94;
    }
    if (pages > 2) console.error(`Warnung: PDF hat ${pages} Seiten`);
    else console.log(`PDF: ${pages} Seiten, Skalierung ${scale.toFixed(3)}`);
  }
  await browser.close();
})();
