// Compose Glass scenes from the captured pages, on the GPU.
//   node render.cjs <layout>:<dark|light>:still:<out.png> ...            one still per job
//   node render.cjs <layout>:<dark|light>:anim:<frames>:<outDir> ...     numbered frames of a loop
//   node render.cjs <layout>:<dark|light>:loop:<out.webp>:<quality> ...  the layout's own loop, as an animated WebP
// Reads docs/readme/build/shots (made by capture.cjs). three and playwright come from NODE_PATH; `loop` needs ffmpeg.
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs'), { pathToFileURL } = require('url'), { execFileSync } = require('child_process');
const SRC = __dirname, SHOTS = path.resolve(SRC, '..', 'build', 'shots');
const THREE_DIR = path.dirname(require.resolve('three'));
const MIME = { '.js': 'text/javascript', '.html': 'text/html', '.png': 'image/png', '.json': 'application/json' };

function file(url) {
  const p = decodeURIComponent(new URL(url).pathname);
  if (p.startsWith('/three/')) return path.join(THREE_DIR, p.slice(7));
  if (p.startsWith('/shots/')) return path.join(SHOTS, p.slice(7));
  return path.join(SRC, p.replace(/^\/src\//, ''));
}

// A loop as an animated WebP. The first frame is encoded whole, as a still would be. Every later frame carries
// only the blocks that differ from what the viewer already has (ffmpeg's conditional replenishment; libwebp_anim
// compares each frame with the one before it instead, so a slow fade never arrives and leaves a ghost), so the
// still glass costs nothing and only the moving part is paid for. Those later frames get a flat quantiser
// (-preset icon), four points higher: the default spends the fewest bits on the busiest blocks of a frame, and in
// a frame that is mostly empty the busiest blocks are the ones being sent, which then land as patches on smooth
// glass. ffmpeg keeps one setting for a whole file, so the frames are encoded with each and the first frame of
// one file is set in front of the later frames of the other.
function encodeLoop(dir, fps, q, out) {
  const enc = (more, to) => execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(fps), '-i', path.join(dir, 'f%04d.png'),
    '-pix_fmt', 'yuva420p', '-c:v', 'libwebp', '-lossless', '0', '-compression_level', '6', '-cr_threshold', '64', '-cr_size', '8',
    '-g', '100000', '-loop', '0', ...more, to]);
  const first = path.join(dir, 'first.webp'), rest = path.join(dir, 'rest.webp');
  enc(['-quality', String(q), '-frames:v', '2'], first);
  enc(['-quality', String(Math.min(100, q + 4)), '-preset', 'icon'], rest);
  const chunks = (f) => {                               // the RIFF chunks after the 12 byte file header
    const d = fs.readFileSync(f), c = [];
    for (let p = 12; p < d.length;) { const n = 8 + d.readUInt32LE(p + 4), e = p + n + (n & 1); c.push(d.subarray(p, e)); p = e; }
    return c;
  };
  const frame = (c) => c.toString('latin1', 0, 4) === 'ANMF';
  const A = chunks(first), B = chunks(rest);
  const body = Buffer.concat([...B.filter(c => !frame(c)), A.find(frame), ...B.filter(frame).slice(1)]);
  const head = Buffer.alloc(12); head.write('RIFF', 0, 'latin1'); head.writeUInt32LE(4 + body.length, 4); head.write('WEBP', 8, 'latin1');
  fs.writeFileSync(out, Buffer.concat([head, body]));
  fs.rmSync(first); fs.rmSync(rest);
}

(async () => {
  const jobs = process.argv.slice(2).map(j => j.split(':'));
  const { LAYOUTS } = await import(pathToFileURL(path.join(SRC, 'layouts.js')).href);
  const browser = await chromium.launch({ args: ['--use-angle=vulkan', '--enable-features=Vulkan', '--ignore-gpu-blocklist', '--enable-gpu'] });
  for (const [layout, theme, mode, a, b] of jobs) {
    const L = LAYOUTS[layout];
    if (!L) throw new Error('unknown layout ' + layout);
    const ctx = await browser.newContext({ viewport: { width: L.css[0], height: L.css[1] }, deviceScaleFactor: L.dpr });
    const page = await ctx.newPage();
    page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text().slice(0, 2000)); });
    page.on('pageerror', e => console.log('[pageerror]', e.message));
    await page.route('http://glass.local/**', r => {
      const f = file(r.request().url());
      if (fs.existsSync(f)) r.fulfill({ path: f, contentType: MIME[path.extname(f)] || 'application/octet-stream' });
      else { console.log('404', path.relative(SRC, f)); r.fulfill({ status: 404, body: '' }); }
    });
    await page.goto(`http://glass.local/src/scene.html?layout=${layout}&theme=${theme}&ss=2`);
    await page.waitForFunction(() => window.__ready !== undefined, null, { timeout: 30000 });
    await page.evaluate(() => window.__ready);
    await page.waitForTimeout(300);
    const t0 = Date.now();
    if (mode === 'still') {
      await page.evaluate(p => window.renderAt(p), 0);
      await page.screenshot({ path: a });
    } else {
      if (mode === 'loop' && !L.loop) throw new Error(layout + ' has no loop');
      const n = mode === 'loop' ? L.loop.frames : +a;
      const dir = mode === 'loop' ? path.resolve(SHOTS, '..', 'loop', `${layout}-${theme}`) : b;
      fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
      for (let i = 0; i < n; i++) {
        await page.evaluate(p => window.renderAt(p), i / n);
        await page.screenshot({ path: path.join(dir, `f${String(i).padStart(4, '0')}.png`) });
      }
      if (mode === 'loop') encodeLoop(dir, L.loop.fps, +b, a);
    }
    console.log(layout, theme, mode, ((Date.now() - t0) / 1000).toFixed(1) + 's');
    await ctx.close();
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
