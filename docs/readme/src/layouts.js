// filmforge in Glass. Every composition shares the profile's spatial grammar: copy flush left on the page
// colour, glass windows of real pages and real tool output on the right, one element lifted out of its page.
// Positions are the apparent centre in CSS px (y down); sizes are apparent CSS px; z is depth
// (+ toward the viewer; 1 unit = 1 px at z = 0). Textures are the pages capture.cjs photographed:
// `<page>-dark.png` and `<page>-light.png`. A lifted element names its box (`box: 'err'`), measured from the page.

// Night: a forge after dark. Warm ink, ember light low in the haze, embers rising, one gold thread.
const NIGHT = {
  page: '#0d1117',
  env: { top: '#0f0d0b', bot: '#070606', haze: '#2a2018', hazeStr: 0.10, ray: '#e8cda2',
    shafts: [[0.50, 0.05, 0.04, 0.09], [0.70, 0.025, 0.02, 0.06], [0.88, 0.07, -0.04, 0.09], [0.72, 0.22, 0.0, 0.035]],
    glows: [[0.70, 0.18, 0.46, 0.09, '#8a4620'], [0.72, 1.1, 0.6, 0.07, '#b09062']],
    thread: [0.46, 0.010, 0.0007, 0.85], threadCol: '#f2b45c' },
  glass: { tint: [0.072, 0.064, 0.056], transmit: 0.80, fog: '#0e0c0a', light: [-700, 800, 900], rim: 0.9, spec: 0.40, glow: 0.55, shadow: 0.30, levels: 5, caustic: 0 },
  motes: { n: 90, color: '#ffb066', amt: 0.62, rise: 1 },
  bloom: 0.42, bloomThresh: 0.55,
};
// Day: warm paper in a sunlit room, leaf shadow on the wall, the same gold thread drawn across it.
const DAY = {
  page: '#ffffff',
  env: { top: '#f5f2ec', bot: '#faf9f6', haze: '#ffffff', hazeStr: 0.04, shadeCol: '#efebe3', sun: [0.42, 0, -1.15, 1.0], dapple: 0.6, sunStr: 0.075, sunCol: '#fff0d4',
    shadow: 0.55, caustic: 0.10, shadowDir: [0.05, -0.075], glows: [],
    thread: [0.46, 0.010, 0.0006, 0.75], threadCol: '#b5853a' },
  glass: { tint: [0.077, 0.076, 0.074], transmit: 0.88, fog: '#f3f0ea', light: [-700, 800, 900], rim: 0.95, spec: 0.30, glow: 0.0, shadow: 0.12, levels: 5, caustic: 0 },
  motes: { n: 40, color: '#fffaf0', amt: 0.45 },
  bloom: 0.0, bloomThresh: 0.95,
};
const merge = (a, b) => { const o = { ...a }; for (const k in b) o[k] = (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k])) ? merge(a[k] || {}, b[k]) : b[k]; return o; };

const C = {
  kick: { night: { color: 'rgba(232,205,162,0.62)' }, day: { color: '#8a7a62' } },
  name: { night: { color: '#f6f1ea' }, day: { color: '#0d0b09' } },
  head: { night: { color: '#f6f1ea' }, day: { color: '#0d0b09' } },
  line: { night: { color: 'rgba(236,228,216,0.74)' }, day: { color: '#4d483f' } },
  fact: { night: { color: '#f2ece3' }, day: { color: '#13110e' } },
  big: { night: { color: '#f4eee5' }, day: { color: '#13110e' } },
  cmd: { night: { color: 'rgba(232,205,162,0.55)' }, day: { color: '#8a7a62' } },
  rule: { night: { background: 'rgba(236,215,180,0.17)' }, day: { background: 'rgba(60,40,20,0.13)' } },
};
const T = (cls, html, x, y, style = {}, align) => ({ cls, html, x, y, align, style, ...C[cls] });
const FACT = (v, l) => `<b>${v}</b><span>${l}</span>`;
const DOC = (n) => n ? '#100E0C' : '#F7F4EE';     // the documents' page colour, keyed away by the glass
const TERM = '#0B0A09';                            // the terminals' background
const tx = (page, n) => `${page}-${n ? 'dark' : 'light'}.png`;
const LIFT = (n) => ({ shadowOff: n ? [0, -16, 40] : [10, -22, 26], shadow: n ? 0.45 : 0.22 });

// ---------- feature panels: copy left, glass right ----------
// o: kick, head (with <br>), line, facts [[value, label] x3], cmd, win(night, phone)
function panel(o) {
  const DY = o.dy ?? -20, ty = (o.ty ?? 92) + DY, hl = o.headLines ?? 2;
  const headY = ty + 24, lineY = headY + hl * 38 + 18, ry = (o.ry ?? 318) + DY;
  return {
    css: [840, o.h || 420], fade: [36, 36, 30, 36], cam: [12, 5], pool: o.pool || [0.69, 0.52, 0.37, 0.66],
    threadSpan: [0.30, 0.48, 0.90, 1.0],
    night: merge(NIGHT, o.night || {}), day: merge(DAY, o.day || {}),
    windows: (n) => o.win(n, false).map((w) => (w.parent !== undefined ? w : { ...w, y: w.y + DY })),
    type: [
      T('kick', o.kick, 2, ty, { fontSize: '10.5px' }),
      T('head', o.head, 0, headY, { fontSize: '36px' }),
      T('line', o.line, 2, lineY, { fontSize: '15.5px', whiteSpace: 'normal', width: '286px' }),
      T('rule', '', 2, ry, { width: '300px' }),
      ...o.facts.map((fc, i) => T('fact', FACT(fc[0], fc[1]), 2 + i * 102, ry + 18, { width: '92px', whiteSpace: 'normal' })),
    ],
  };
}
function panelPhone(o) {
  const ry = o.ryp ?? 548;
  return {
    css: [381, o.hp || 680], dpr: 1080 / 381, fade: [18, 18, 24, 28], cam: [8, 4], pool: o.poolPhone || [0.5, 0.40, 0.70, 0.34],
    threadSpan: [0.0, 0.2, 0.8, 1.0],
    night: merge(merge(NIGHT, o.night || {}), { env: { thread: [o.threadPhone ?? 0.40, 0.008, 0.0006, 0.85] } }),
    day: merge(merge(DAY, o.day || {}), { env: { thread: [o.threadPhone ?? 0.40, 0.008, 0.0005, 0.75] } }),
    windows: (n) => o.win(n, true),
    type: [
      T('kick', o.kick, 4, 26, { fontSize: '9.5px' }),
      T('head', o.head.replace(/<br>/g, ' '), 2, 46, { fontSize: '31px', whiteSpace: 'normal', width: '360px' }),
      T('line', o.line, 4, 46 + (o.headLinesPhone ?? 2) * 33 + 14, { fontSize: '15px', whiteSpace: 'normal', width: '352px' }),
      T('rule', '', 4, ry, { width: '372px' }),
      ...o.facts.map((fc, i) => T('fact', FACT(fc[0], fc[1]), 4 + i * 124, ry + 18, { width: '112px', whiteSpace: 'normal' })),
    ],
  };
}

const PRICE = {
  kick: 'Budget<i>budget.py</i>', head: 'Priced before<br>the first credit',
  line: 'Every sheet, plate, painting and cue is priced against the credits, with a retake buffer per stage and a reserve that is never spent.',
  facts: [['39.08', 'credits planned, with retakes'], ['5%', 'reserve, never spent'], ['27.42', 'credits to spare']],
  win: (n, ph) => {
    const P = ph ? { a: { x: 188, y: 380, w: 334, z: -40, rot: [2, -8, 0] } } : { a: { x: 590, y: 240, w: 404, z: -60, rot: [2, -16, 0] } };
    return [
      { tex: tx('term-budget', n), ...P.a, key: TERM, keyAmt: n ? 0.6 : 0.12, breathe: [8, 0.0], bezel: 10, glowColor: '#3a2412' },
      { parent: 0, box: 'fits', pad: [18, 6], lift: 90, align: 0.9, breathe: [10, 0.25], bezel: 8, radius: 12, key: TERM, keyAmt: n ? 0.7 : 0.25, ...LIFT(n), glow: 0.3, glowColor: '#28472f' },
    ];
  },
};
const PROMPT = {
  kick: 'Prompt grammar<i>forge-painter</i>', head: 'Twelve slots,<br>every prompt',
  line: 'Look, references, shot, subject and scale, moment, setting, light, colour, text area, continuity, locks, avoid. The order never changes, so a missing slot shows.',
  facts: [['12', 'slots, always in order'], ['1', 'look sentence, word for word'], ['3,500', 'characters at most']],
  h: 470, ry: 340,
  win: (n, ph) => {
    const P = ph ? { a: { x: 190, y: 380, h: 300, z: -40, rot: [2, -8, 0] } } : { a: { x: 596, y: 236, h: 352, z: -60, rot: [2, -16, 0] } };
    return [
      { tex: tx('prompt', n), ...P.a, key: DOC(n), keyAmt: n ? 0.55 : 0.72, breathe: [8, 0.0], bezel: 11 },
      { parent: 0, box: 'scale', pad: [14, 4], lift: 90, align: 0.7, breathe: [10, 0.25], bezel: 9, radius: 12, key: DOC(n), keyAmt: n ? 0.6 : 0.85, ...LIFT(n), glow: 0.25, glowColor: '#5a3d16' },
    ];
  },
};
const LINT = {
  kick: 'Prompt lint<i>ledger.py</i>', head: 'Linted before<br>it is painted',
  line: 'Every prompt is checked against the style lock and the continuity ledger. The paint gate stays shut until it passes.',
  headLinesPhone: 1,
  facts: [['6', 'prompts checked'], ['1', 'error: a lost scale lock'], ['FAIL', 'the paint gate, until it passes']],
  win: (n, ph) => {
    const P = ph ? { a: { x: 170, y: 350, w: 320, z: -60, rot: [2, -10, 0] }, b: { x: 236, y: 448, w: 270, z: 70, rot: [0, -12, 0] } }
      : { a: { x: 556, y: 206, w: 380, z: -80, rot: [2, -18, 0] }, b: { x: 664, y: 318, w: 300, z: 60, rot: [0, -14, 0] } };
    return [
      { tex: tx('term-gate', n), ...P.a, key: TERM, keyAmt: n ? 0.6 : 0.12, breathe: [8, 0.0], bezel: 10, glowColor: '#2e2010' },
      { tex: tx('term-lint', n), ...P.b, key: TERM, keyAmt: n ? 0.6 : 0.12, breathe: [8, 0.45], bezel: 9, glowColor: '#3a1c12' },
      { parent: 1, box: 'err', pad: [16, 6], lift: 80, align: 0.9, breathe: [10, 0.25], bezel: 8, radius: 12, key: TERM, keyAmt: n ? 0.7 : 0.25, ...LIFT(n), glow: 0.35, glowColor: '#5a2214' },
    ];
  },
};
const SHOTS = {
  kick: 'Shot list<i>shotlist.py</i>', head: 'A shot list the<br>tools can read',
  line: 'Validated against the schema and the ledger, measured scene by scene, and retimed frame-exact onto the measured score.',
  hp: 724, ryp: 598,
  facts: [['6', 'shots, no problems'], ['36.2 s', 'at 24 frames a second'], ['67%', 'of the film holds the moth']],
  win: (n, ph) => {
    const P = ph ? { a: { x: 168, y: 350, w: 320, z: -60, rot: [2, -10, 0] }, b: { x: 262, y: 446, w: 200, z: 70, rot: [0, -12, 0] } }
      : { a: { x: 556, y: 214, w: 372, z: -80, rot: [2, -18, 0] }, b: { x: 698, y: 322, w: 200, z: 60, rot: [0, -14, 0] } };
    return [
      { tex: tx('term-shotlist', n), ...P.a, key: TERM, keyAmt: n ? 0.6 : 0.12, breathe: [8, 0.0], bezel: 10, glowColor: '#2e2010' },
      { tex: tx('yaml-shot', n), ...P.b, key: TERM, keyAmt: n ? 0.6 : 0.12, breathe: [8, 0.45], bezel: 9, glowColor: '#3a2a12' },
      { parent: 0, box: 'ok', pad: [18, 6], lift: 90, align: 0.9, breathe: [10, 0.25], bezel: 8, radius: 12, key: TERM, keyAmt: n ? 0.7 : 0.25, ...LIFT(n), glow: 0.3, glowColor: '#28472f' },
    ];
  },
};

// ---------- the hero ----------
const HERO_NIGHT = merge(NIGHT, { env: {
  shafts: [[0.30, 0.050, 0.05, 0.13], [0.42, 0.020, 0.02, 0.10], [0.58, 0.022, -0.02, 0.11], [0.71, 0.050, -0.05, 0.13], [0.50, 0.22, 0.0, 0.06]],
  glows: [[0.50, 0.30, 0.42, 0.12, '#8a4620'], [0.5, 1.15, 0.65, 0.09, '#b09062'], [0.5, -0.15, 0.6, 0.05, '#5a3a22']],
  thread: [0.50, 0.012, 0.0008, 0.9] } });
const HERO_DAY = merge(DAY, { env: { sun: [0.10, 0, -0.80, 0.95], thread: [0.50, 0.012, 0.0006, 0.8] } });
const HERO_FRAMES = 96;                            // the hero loop, 8 s at 12 fps: as many frames as pages/track.html draws
const HERO_LOOP = { frames: HERO_FRAMES, fps: 12 };
const RAIL = (n) => Array.from({ length: HERO_FRAMES }, (_, i) => `track-${n ? 'dark' : 'light'}-${String(i).padStart(2, '0')}.png`);
const heroWindows = (n, P) => [
  { tex: tx('term-budget', n), key: TERM, keyAmt: n ? 0.62 : 0.15, fog: n ? 0.58 : 0.38, lod: 1.2, defocus: 2.5, breathe: [16, 0.15], bezel: 8, glowColor: '#2e2010' },
  { tex: tx('term-status', n), key: TERM, keyAmt: n ? 0.62 : 0.15, fog: n ? 0.58 : 0.38, lod: 1.2, defocus: 2.5, breathe: [12, 0.8], bezel: 8, glowColor: '#2e2010' },
  { tex: tx('prompt', n), crop: [0, 0, 1320, 1180], key: DOC(n), keyAmt: n ? 0.55 : 0.75, breathe: [12, 0.5], lod: 0.4, defocus: 0.8, fog: n ? 0.18 : 0.10 },
  { tex: tx('term-shotlist', n), key: TERM, keyAmt: n ? 0.6 : 0.15, breathe: [12, 0.0], lod: 0.4, defocus: 0.8, fog: n ? 0.18 : 0.10, glowColor: '#2e2010' },
  { tex: tx('method', n), key: DOC(n), keyAmt: n ? 0.55 : 0.75, breathe: [10, 0.6], bezel: 11, glow: 0.6 },
  { tex: tx('term-lint', n), key: TERM, keyAmt: n ? 0.6 : 0.15, breathe: [9, 0.3], bezel: 9, glowColor: '#3a1c12' },
  { parent: 4, box: 'lint', pad: [10, 4], lift: 110, align: 0.6, breathe: [12, 0.85], bezel: 8, radius: 12, key: DOC(n), keyAmt: n ? 0.6 : 0.85, ...LIFT(n), glow: 0.25, glowColor: '#5a3d16' },
  // the stage rail: the one thing in the hero that moves. Its frames are the captures of pages/track.html
  { seq: RAIL(n), key: DOC(n), keyAmt: n ? 0.55 : 0.75, bar: false, bezel: 6, radius: 13, breathe: [6, 0.3], glow: 0.3, glowColor: '#5a3d16' },
].map((w, i) => ({ ...w, ...(P[i] || {}) }));

// ---------- the numbers band and the stages diagram ----------
const NUMBERS = [['9', 'Claude Code skills,<br>one per stage'], ['7', 'tools that check,<br>price and measure'], ['12', 'slots in every<br>prompt, in order'], ['40', 'tests in CI']];

export const LAYOUTS = {
  hero: {
    css: [840, 560], fade: [40, 40, 30, 46], cam: [3, 1.2], motion: 0.2, hold: 1, loop: HERO_LOOP, pool: [0.5, 0.42, 0.62, 0.62], threadSpan: [0.0, 0.16, 0.84, 1.0],
    night: HERO_NIGHT, day: HERO_DAY,
    windows: (n) => heroWindows(n, [
      { x: 104, y: 204, w: 112, z: -820, rot: [10, 18, 0] },
      { x: 738, y: 204, w: 108, z: -820, rot: [10, -18, 0] },
      { x: 128, y: 330, w: 196, z: -320, rot: [2, 32, 0] },
      { x: 716, y: 316, w: 206, z: -320, rot: [2, -32, 0] },
      { x: 404, y: 344, w: 280, z: 40, rot: [3, 0, 0] },
      { x: 648, y: 452, w: 262, z: 170, rot: [0, -14, 0] },
      ,
      { x: 420, y: 161, w: 322, z: 20, rot: [5, 0, 0] },
    ]),
    type: [
      T('name', 'filmforge', 420, 34, { fontSize: '60px' }, 'center'),
      T('line', 'The technique for painted films made with AI, written down and checked at every gate.', 420, 110, { fontSize: '16.5px' }, 'center'),
    ],
  },
  'hero-phone': {
    css: [381, 640], dpr: 1080 / 381, fade: [16, 16, 24, 30], cam: [7, 3], motion: 0.75, hold: 2, loop: HERO_LOOP, pool: [0.5, 0.40, 0.75, 0.55], threadSpan: [0.0, 0.2, 0.8, 1.0],
    night: merge(HERO_NIGHT, { env: { thread: [0.42, 0.010, 0.0007, 0.9] } }), day: merge(HERO_DAY, { env: { thread: [0.42, 0.010, 0.0005, 0.8] } }),
    windows: (n) => heroWindows(n, [
      { x: 90, y: 228, w: 92, z: -820, rot: [10, 18, 0] },
      { x: 294, y: 226, w: 90, z: -820, rot: [10, -18, 0] },
      { x: 70, y: 318, w: 136, z: -320, rot: [2, 32, 0] },
      { x: 314, y: 306, w: 136, z: -320, rot: [2, -32, 0] },
      { x: 182, y: 388, w: 262, z: 40, rot: [3, 0, 0] },
      { x: 270, y: 512, w: 196, z: 170, rot: [0, -14, 0] },
      ,
      { x: 190.5, y: 190, w: 316, z: 20, rot: [5, 0, 0] },
    ]),
    type: [
      T('name', 'filmforge', 190.5, 34, { fontSize: '52px' }, 'center'),
      T('line', 'The technique for painted films made with AI,<br>written down and checked at every gate.', 190.5, 102, { fontSize: '14.5px', textAlign: 'center' }, 'center'),
    ],
  },
  numbers: {
    css: [840, 168], fade: [30, 30, 20, 20], cam: [6, 2], pool: [0.5, 0.5, 0.75, 1.4], threadSpan: [0.0, 0.12, 0.88, 1.0],
    night: merge(NIGHT, { env: { thread: [0.5, 0.05, 0.0012, 0.75], glows: [[0.5, 0.5, 0.5, 0.06, '#8a4620']] }, motes: { n: 14 } }),
    day: merge(DAY, { env: { thread: [0.5, 0.05, 0.0010, 0.6] }, motes: { n: 8 } }),
    windows: () => [{ x: 420, y: 84, w: 776, crop: [0, 0, 776, 100], z: 0, rot: [0, 0, 0], bar: false, bezel: 12, radius: 26, breathe: [4, 0], glow: 0.0, shadowOff: [0, -10, 36] }],
    type: NUMBERS.map(([v, l], i) => T('big', `<b style="font-size:42px">${v}</b><span style="font-size:13px;margin-top:9px">${l}</span>`, 58 + i * 196, 40)),
  },
  'numbers-phone': {
    css: [381, 330], dpr: 1080 / 381, fade: [16, 16, 18, 18], cam: [4, 2], pool: [0.5, 0.5, 0.8, 1.2], threadSpan: [0.0, 0.15, 0.85, 1.0],
    night: merge(NIGHT, { env: { thread: [0.5, 0.03, 0.0008, 0.75], glows: [[0.5, 0.5, 0.5, 0.06, '#8a4620']] }, motes: { n: 12 } }),
    day: merge(DAY, { env: { thread: [0.5, 0.03, 0.0007, 0.6] }, motes: { n: 6 } }),
    windows: () => [{ x: 190.5, y: 165, w: 337, crop: [0, 0, 337, 266], z: 0, rot: [0, 0, 0], bar: false, bezel: 12, radius: 24, breathe: [3, 0], glow: 0.0, shadowOff: [0, -10, 30] }],
    type: NUMBERS.map(([v, l], i) => T('big', `<b style="font-size:40px">${v}</b><span style="font-size:13px;margin-top:8px">${l}</span>`, 38 + (i % 2) * 172, 46 + Math.floor(i / 2) * 134)),
  },
  stages: {
    css: [840, 250], fade: [30, 30, 22, 26], cam: [8, 3], pool: [0.5, 0.5, 0.72, 1.1], threadSpan: [0.0, 0.1, 0.9, 1.0],
    night: merge(NIGHT, { env: { thread: [0.62, 0.02, 0.0009, 0.6], glows: [[0.55, 0.45, 0.45, 0.07, '#8a4620']] }, motes: { n: 18 } }),
    day: merge(DAY, { env: { thread: [0.62, 0.02, 0.0007, 0.5] }, motes: { n: 8 } }),
    windows: (n) => [{ tex: tx('stages', n), x: 420, y: 116, w: 790, z: 0, rot: [3, 0, 0], key: DOC(n), keyAmt: n ? 0.55 : 0.72, bezel: 10, breathe: [5, 0], glow: 0.3, bar: false }],
    type: [],
  },
  'stages-phone': {
    css: [381, 640], dpr: 1080 / 381, fade: [16, 16, 20, 24], cam: [5, 3], pool: [0.5, 0.5, 0.8, 0.8], threadSpan: [0.0, 0.15, 0.85, 1.0],
    night: merge(NIGHT, { env: { thread: [0.70, 0.015, 0.0008, 0.6] }, motes: { n: 18 } }),
    day: merge(DAY, { env: { thread: [0.70, 0.015, 0.0006, 0.5] }, motes: { n: 8 } }),
    windows: (n) => [{ tex: tx('stages-phone', n), x: 190.5, y: 300, w: 345, z: 0, rot: [2, 0, 0], key: DOC(n), keyAmt: n ? 0.55 : 0.72, bezel: 10, breathe: [5, 0], glow: 0.3, bar: false }],
    type: [],
  },
  price: panel(PRICE), 'price-phone': panelPhone(PRICE),
  prompt: panel(PROMPT), 'prompt-phone': panelPhone(PROMPT),
  lint: panel(LINT), 'lint-phone': panelPhone(LINT),
  shots: panel(SHOTS), 'shots-phone': panelPhone(SHOTS),
};
for (const k in LAYOUTS) LAYOUTS[k].dpr = LAYOUTS[k].dpr || 2;
