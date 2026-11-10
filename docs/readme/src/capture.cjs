// Capture every page the Glass scenes show, at 2x, in the dark and the light colour scheme.
//   node capture.cjs
// Pages: docs/readme/src/pages/*.html (written by hand from the repository's own text) and
// docs/readme/build/pages/*.html (written by terminals.py from the tools' real output).
// A page sets its size with <meta name="size" content="W" or "WxH">. Elements marked data-lift="id"
// are measured into build/shots/boxes.json, so a scene can lift them out of the page by name.
// A page that moves says so with <meta name="frames" content="N"> and draws frame i of its loop in
// window.frame(i, N); each frame is photographed as <page>-<scheme>-NN.png for the hero loop.
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs'), { pathToFileURL } = require('url');
const SRC = __dirname, BUILD = path.resolve(SRC, '..', 'build'), SHOTS = path.join(BUILD, 'shots');
const DSF = 2;

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const pages = [path.join(SRC, 'pages'), path.join(BUILD, 'pages')]
    .flatMap(d => fs.existsSync(d) ? fs.readdirSync(d).filter(f => f.endsWith('.html')).map(f => path.join(d, f)) : []);
  const browser = await chromium.launch();
  const boxes = {};
  for (const scheme of ['dark', 'light']) {
    const ctx = await browser.newContext({ viewport: { width: 800, height: 600 }, deviceScaleFactor: DSF, colorScheme: scheme });
    const page = await ctx.newPage();
    for (const f of pages) {
      const name = path.basename(f, '.html');
      const html = fs.readFileSync(f, 'utf8');
      const m = html.match(/<meta name="size" content="(\d+)(?:x(\d+))?">/);
      if (!m) throw new Error(name + ': no <meta name="size">');
      const w = +m[1];
      await page.setViewportSize({ width: w, height: +(m[2] || 400) });
      await page.goto(pathToFileURL(f).href, { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      const h = m[2] ? +m[2] : await page.evaluate(() => Math.ceil(document.body.getBoundingClientRect().height));
      await page.setViewportSize({ width: w, height: h });
      await page.waitForTimeout(150);
      boxes[name] = await page.evaluate((k) => Object.fromEntries([...document.querySelectorAll('[data-lift]')].map(e => {
        const r = e.getBoundingClientRect(); return [e.dataset.lift, [r.x * k, r.y * k, r.width * k, r.height * k].map(Math.round)];
      })), DSF);
      await page.screenshot({ path: path.join(SHOTS, `${name}-${scheme}.png`) });
      const fr = html.match(/<meta name="frames" content="(\d+)">/);
      for (let i = 0; fr && i < +fr[1]; i++) {
        await page.evaluate(([i, n]) => window.frame(i, n), [i, +fr[1]]);
        await page.screenshot({ path: path.join(SHOTS, `${name}-${scheme}-${String(i).padStart(2, '0')}.png`) });
      }
      console.log(`${name}-${scheme}`, `${w}x${h}`);
    }
    await ctx.close();
  }
  fs.writeFileSync(path.join(SHOTS, 'boxes.json'), JSON.stringify(boxes, null, 1));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
