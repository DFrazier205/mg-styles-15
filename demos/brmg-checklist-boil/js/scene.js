// BRMG notebook checklist — cel animation / line boil, 9:16, 15 s.
// Every frame is a pure function of t. Drawings are animated on 2s (12 drawings/s) with a 4-drawing boil cycle;
// the camera slide is on 1s so motion blur can smooth it. All timing comes from cues.json.
import {
  mulberry32, hs, clamp, lerp, inv, sstep, K,
  spline, resample, prefix, boil, fillPoly, polyPath,
  inkStroke, inkLoop, circlePts,
} from '/demos/05-cel-boil/js/engine.js';

export const W = 1080, H = 1920, FPS = 24, DURATION = 15;

// BRMG tokens (brand design system, Oct 2026)
const CH = '#3D3935';    // Charcoal Espresso — all line work and lettering
const RED = '#DB1F1F';   // Impact Red — ticks, underline, margin rule, small accents only
const PAPER = '#F2F1ED'; // Paper Warm — the page
const GREY = '#E8E8E8';  // Paper Grey — punch-hole shading

const WORLD_H = 3900;
const RULE = 72;          // ruled-line pitch
const RULE0 = 90;         // first ruled line
const MARGIN_X = 120;     // red margin rule
const BOX_CX = 225, BOX = 120, WORD_X = 325, ICON_CX = 905;
const WORD_SIZE = 112;
const ROW_BASE0 = RULE0 + RULE * 8;   // 666: baseline of the first item, sits on a ruled line
const ROW_PITCH = RULE * 5;           // 360

let ctx, cv, CUES, GRAIN, FONT = {}, CAP = 80;
let V = 0;          // boil drawing index 0..3 (re-rolled every 2 frames)
const sd = (id) => id * 4 + V;

// ------------------------------------------------------------------ init
async function loadFont(ot, url) { return ot.parse(await (await fetch(url)).arrayBuffer()); }

function makeGrain() {
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const x = c.getContext('2d');
  const cc = document.createElement('canvas'); cc.width = 68; cc.height = 120;
  const cx = cc.getContext('2d'); const id = cx.createImageData(68, 120); const r = mulberry32(7);
  for (let i = 0; i < 68 * 120; i++) { const v = 247 + Math.floor(r() * 9); id.data[i * 4] = id.data[i * 4 + 1] = id.data[i * 4 + 2] = v; id.data[i * 4 + 3] = 255; }
  cx.putImageData(id, 0, 0);
  x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high';
  x.drawImage(cc, 0, 0, W, H);
  const fi = x.getImageData(0, 0, W, H), d = fi.data, r2 = mulberry32(99);
  for (let i = 0; i < d.length; i += 4) {
    const n = (r2() + r2() + r2()) / 3;
    const k = 1 - (0.5 - n) * 0.06 - (r2() < 0.012 ? 0.035 : 0);
    d[i] = Math.min(255, d[i] * k); d[i + 1] = Math.min(255, d[i + 1] * k); d[i + 2] = Math.min(255, d[i + 2] * k);
  }
  x.putImageData(fi, 0, 0);
  return c;
}

export async function init(canvas, dpr = 1) {
  cv = canvas; cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
  ctx = cv.getContext('2d');
  CUES = await (await fetch('/demos/brmg-checklist-boil/cues.json')).json();
  const m = await import('opentype'); const ot = m.parse ? m : m.default;
  FONT.anton = await loadFont(ot, '/assets/fonts/latin/anton/Anton-Regular.ttf');
  FONT.bagel = await loadFont(ot, '/assets/fonts/latin/bagelfatone/BagelFatOne-Regular.ttf');
  CAP = -FONT.anton.getPath('H', 0, 0, WORD_SIZE).getBoundingBox().y1;
  GRAIN = makeGrain();
}

// ------------------------------------------------------------------ hand lettering from real glyph outlines
function flatten(cmds) {
  const cs = []; let cur = null;
  for (const c of cmds) {
    if (c.type === 'M') { if (cur && cur.length > 2) cs.push(cur); cur = [[c.x, c.y]]; }
    else if (c.type === 'L') cur.push([c.x, c.y]);
    else if (c.type === 'Q') {
      const p0 = cur[cur.length - 1];
      for (let k = 1; k <= 10; k++) { const t = k / 10, u = 1 - t; cur.push([u * u * p0[0] + 2 * u * t * c.x1 + t * t * c.x, u * u * p0[1] + 2 * u * t * c.y1 + t * t * c.y]); }
    } else if (c.type === 'C') {
      const p0 = cur[cur.length - 1];
      for (let k = 1; k <= 12; k++) {
        const t = k / 12, u = 1 - t;
        cur.push([u * u * u * p0[0] + 3 * u * u * t * c.x1 + 3 * u * t * t * c.x2 + t * t * t * c.x,
                  u * u * u * p0[1] + 3 * u * u * t * c.y1 + 3 * u * t * t * c.y2 + t * t * t * c.y]);
      }
    } else if (c.type === 'Z') { if (cur && cur.length > 2) cs.push(cur); cur = null; }
  }
  if (cur && cur.length > 2) cs.push(cur);
  return cs;
}
const GCACHE = new Map();
function glyph(fk, ch, size) {
  const key = fk + ch + size;
  if (GCACHE.has(key)) return GCACHE.get(key);
  const f = FONT[fk], p = f.getPath(ch, 0, 0, size), bb = p.getBoundingBox();
  const g = { contours: flatten(p.commands).map((c) => resample(c, 3.6, true)), cx: (bb.x1 + bb.x2) / 2, cy: (bb.y1 + bb.y2) / 2 };
  GCACHE.set(key, g);
  return g;
}
function layout(fk, text, size, track = 0) {
  const f = FONT[fk], k = size / f.unitsPerEm, items = [];
  let x = 0;
  for (let i = 0; i < text.length; i++) {
    const g = f.charToGlyph(text[i]);
    items.push({ ch: text[i], x });
    let adv = g.advanceWidth * k;
    if (i < text.length - 1) adv += f.getKerningValue(g, f.charToGlyph(text[i + 1])) * k;
    x += adv + track;
  }
  return { items, width: x - track };
}
// letters pop in one by one, each re-rolled by the boil
function drawText(o) {
  const { fk, text, size, x, baseline, align = 'left', t, start, stagger = 0.045, dur = 0.18, seed, color = CH, amp = 1.6, w = 3.2 } = o;
  const L = layout(fk, text, size);
  const x0 = align === 'center' ? x - L.width / 2 : x;
  ctx.fillStyle = color; ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineJoin = 'round';
  L.items.forEach((it, i) => {
    if (it.ch === ' ') return;
    const u = (t - (start + i * stagger)) / dur;
    if (u <= 0) return;
    const pop = u >= 1 ? 1 : K(u, [[0, 0.25], [0.55, 1.2, 'out2'], [1, 1, 'io2']]);
    const rot = (1 - clamp(u)) * (hs(seed, i) - 0.5) * 0.55 + (hs(seed, i, 5) - 0.5) * 0.045;
    const ty = (hs(seed, i, 9) - 0.5) * 5;
    const sc = pop * (1 + (hs(seed, i, 3) - 0.5) * 0.05);
    const g = glyph(fk, it.ch, size);
    const gx = x0 + it.x + g.cx, gy = baseline + g.cy + ty;
    const c = Math.cos(rot), s = Math.sin(rot);
    ctx.beginPath();
    g.contours.forEach((ct, ci) => {
      let pts = ct.map(([px, py]) => {
        const lx = (px - g.cx) * sc, ly = (py - g.cy) * sc;
        return [gx + lx * c - ly * s, gy + lx * s + ly * c];
      });
      pts = boil(pts, sd(seed + i * 0.01 + ci * 0.003), amp, 38);
      polyPath(ctx, pts);
    });
    ctx.fill('nonzero'); ctx.stroke();
  });
  return { width: L.width, x0 };
}

// ------------------------------------------------------------------ ink helpers
function stroke(P, o) {
  const frac = o.frac ?? 1;
  if (frac <= 0) return;
  let pts = resample(spline(P, false, 5), 3.2);
  if (frac < 1) pts = prefix(pts, frac);
  if (pts.length < 2) return;
  inkStroke(ctx, pts, { dense: true, seed: o.seed, amp: o.amp ?? 2, scale: o.scale ?? 60, w: o.w ?? 7, color: o.color ?? CH, t0: o.t0 ?? 10, t1: o.t1 ?? 18, jit: 0.3, heavy: 0.25 });
}
function loop(P, o) { inkLoop(ctx, spline(P, true, 5), { seed: o.seed, amp: o.amp ?? 1.8, scale: o.scale ?? 60, w: o.w ?? 7, color: o.color ?? CH, splits: 1, jit: 0.3, heavy: 0.25 }); }
function circ(cx, cy, r, o) { inkLoop(ctx, circlePts(cx, cy, r), { seed: o.seed, amp: o.amp ?? 1.4, scale: o.scale ?? 50, w: o.w ?? 6, color: o.color ?? CH, splits: 1, jit: 0.3, heavy: 0.25 }); }
function dot(cx, cy, r, seed, color = RED) { fillPoly(ctx, boil(circlePts(cx, cy, r, 18), seed, 1.2, 30), color); }
function arc(cx, cy, r, a0, a1, n = 14) { const p = []; for (let i = 0; i <= n; i++) { const a = lerp(a0, a1, i / n); p.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); } return p; }
const rr = (x0, y0, x1, y1, r) => [[x0 + r, y0], [x1 - r, y0], [x1, y0 + r], [x1, y1 - r], [x1 - r, y1], [x0 + r, y1], [x0, y1 - r], [x0, y0 + r]];

// ------------------------------------------------------------------ doodle icons (local coords, ~ +-96 px)
function iconCalendar(b) {
  loop(rr(-80, -58, 80, 82, 16), { seed: sd(b + 1) });
  stroke([[-80, -18], [80, -18]], { seed: sd(b + 2) });
  stroke([[-38, -86], [-38, -42]], { seed: sd(b + 3), w: 11, t0: 4, t1: 4 });
  stroke([[38, -86], [38, -42]], { seed: sd(b + 4), w: 11, t0: 4, t1: 4 });
  let k = 5;
  for (const r of [20, 54]) for (const c of [-44, 0, 44]) {
    if (r === 54 && c === 44) continue;
    stroke([[c - 11, r], [c + 11, r]], { seed: sd(b + k++), w: 6, t0: 4, t1: 4, amp: 1.2 });
  }
  circ(44, 54, 23, { seed: sd(b + 20), w: 6, color: RED });
}
function iconMic(b) {
  loop(rr(-30, -96, 30, 6, 30), { seed: sd(b + 1) });
  stroke([[-30, -66], [30, -66]], { seed: sd(b + 2), w: 5, amp: 1.2 });
  stroke([[-30, -38], [30, -38]], { seed: sd(b + 3), w: 5, amp: 1.2 });
  stroke([[-58, -30], [-48, 12], [0, 46], [48, 12], [58, -30]], { seed: sd(b + 4) });
  stroke([[0, 46], [0, 92]], { seed: sd(b + 5) });
  stroke([[-38, 94], [38, 94]], { seed: sd(b + 6), w: 9 });
  stroke(arc(0, -45, 76, -0.62, 0.62), { seed: sd(b + 7), w: 7, color: RED });
  stroke(arc(0, -45, 76, Math.PI - 0.62, Math.PI + 0.62), { seed: sd(b + 8), w: 7, color: RED });
}
function iconCamera(b) {
  loop(rr(-86, -38, 86, 66, 16), { seed: sd(b + 1) });
  stroke([[-34, -38], [-22, -64], [24, -64], [36, -38]], { seed: sd(b + 2) });
  circ(0, 14, 40, { seed: sd(b + 3) });
  circ(0, 14, 21, { seed: sd(b + 4), w: 5 });
  stroke([[52, -22], [72, -22]], { seed: sd(b + 5), w: 9, t0: 4, t1: 4 });
  dot(-62, -12, 8, sd(b + 6));
}
function iconPhone(b) {
  loop(rr(-46, -90, 46, 90, 18), { seed: sd(b + 1) });
  loop(rr(-33, -64, 33, 50, 6), { seed: sd(b + 2), w: 5, amp: 1.2 });
  stroke([[-14, -77], [14, -77]], { seed: sd(b + 3), w: 5, amp: 1.2 });
  circ(0, 70, 8, { seed: sd(b + 4), w: 5 });
  stroke([[-20, -38], [18, -38]], { seed: sd(b + 5), w: 5, amp: 1.2 });
  stroke([[-20, -14], [6, -14]], { seed: sd(b + 6), w: 5, amp: 1.2 });
  dot(36, -64, 17, sd(b + 7));
}
const ICONS = { calendar: iconCalendar, mic: iconMic, camera: iconCamera, phone: iconPhone };

// ------------------------------------------------------------------ one checklist row
function drawRow(i, ta) {
  const s = CUES.rows[i], R = CUES.rel;
  const baseY = ROW_BASE0 + ROW_PITCH * i;
  const rowY = baseY - CAP / 2;
  const b = 100 + i * 40;

  // checkbox — drawn on by hand, slightly wonky
  const tb = s + R.box;
  if (ta >= tb) {
    const j = (k) => (hs(i, k, 1) - 0.5) * 9;
    const x0 = BOX_CX - BOX / 2, x1 = BOX_CX + BOX / 2, y0 = rowY - BOX / 2, y1 = rowY + BOX / 2;
    const TL = [x0 + j(1), y0 + j(2)], TR = [x1 + j(3), y0 + j(4)], BR = [x1 + j(5), y1 + j(6)], BL = [x0 + j(7), y1 + j(8)];
    stroke([[TL[0] + 8, TL[1] + 2], [TR[0], TR[1], 1], [BR[0], BR[1], 1], [BL[0], BL[1], 1], [TL[0] - 2, TL[1] - 1, 1], [TL[0] + 30, TL[1] - 2]],
      { seed: sd(b + 1), w: 8, amp: 2, frac: inv(tb, tb + 0.3, ta), t0: 8, t1: 12 });
  }

  // word — hand-lettered, letter by letter (Anton)
  drawText({ fk: 'anton', text: CUES.items[i], size: WORD_SIZE, x: WORD_X, baseline: baseY, t: ta, start: s + R.word, stagger: 0.045, dur: 0.18, seed: b + 7 });

  // red scribbled tick — two passes
  const tt = s + R.tick;
  if (ta >= tt) {
    const bx = BOX_CX + 6, by = rowY - 8;
    stroke([[bx - 52, by + 4], [bx - 16, by + 46, 1], [bx + 78, by - 74]], { seed: sd(b + 2), w: 12, color: RED, amp: 2.2, frac: inv(tt, tt + 0.17, ta), t0: 6, t1: 14 });
    stroke([[bx + 84, by - 62], [bx - 6, by + 56, 1], [bx - 52, by + 12]], { seed: sd(b + 3), w: 10, color: RED, amp: 2.2, frac: inv(tt + 0.17, tt + 0.33, ta), t0: 6, t1: 14 });
  }

  // doodle icon bounces in
  const u = ta - (s + R.icon);
  if (u >= 0) {
    const ty = K(u, [[0, -150], [0.13, 0, 'in2'], [0.24, -38, 'out2'], [0.34, 0, 'in2'], [0.42, -10, 'out2'], [0.5, 0, 'in2']]);
    const sq = K(u, [[0, 0], [0.13, 0], [0.17, 1, 'out2'], [0.28, 0], [0.34, 0], [0.37, 0.5, 'out2'], [0.46, 0]]);
    const st = u < 0.13 ? u / 0.13 : 0;
    let sx = 1 + 0.2 * sq - 0.06 * st, sy = 1 - 0.2 * sq + 0.12 * st;
    const pop = sstep(0, 0.06, u);
    let rot = (1 - sstep(0, 0.5, u)) * 0.12 * Math.sin(u * 28);
    if (u > 0.6) { rot += 0.014 * Math.sin(ta * 5 + i); const br = 1 + 0.014 * Math.sin(ta * 6 + i * 2); sx *= br; sy *= br; }
    ctx.save();
    ctx.translate(ICON_CX, rowY + ty); ctx.rotate(rot); ctx.scale(sx * pop, sy * pop);
    ICONS[CUES.icons[i]](b + 20);
    ctx.restore();
  }
}

// ------------------------------------------------------------------ page furniture
function drawPage(camY) {
  // ruled lines
  ctx.save();
  ctx.strokeStyle = CH; ctx.lineWidth = 2.4; ctx.globalAlpha = 0.15; ctx.lineJoin = 'round';
  const k0 = Math.max(0, Math.floor((camY - RULE0) / RULE)), k1 = Math.ceil((camY + H - RULE0) / RULE);
  for (let k = k0; k <= k1; k++) {
    const y = RULE0 + RULE * k;
    if (y > WORLD_H) break;
    const pts = boil(resample([[0, y], [W, y]], 28), 900 + V * 3 + 0.0, 1.5, 150);
    ctx.beginPath(); polyPath(ctx, pts, false); ctx.stroke();
  }
  ctx.restore();
  // red margin rule
  {
    const pts = boil(resample([[MARGIN_X, camY - 40], [MARGIN_X, camY + H + 40]], 36), 950 + V * 3, 1.6, 150);
    ctx.save(); ctx.strokeStyle = RED; ctx.lineWidth = 3; ctx.globalAlpha = 0.9; ctx.lineJoin = 'round';
    ctx.beginPath(); polyPath(ctx, pts, false); ctx.stroke(); ctx.restore();
  }
  // punch holes
  for (let h = 0; h < 5; h++) {
    const y = 300 + h * 800;
    if (y < camY - 60 || y > camY + H + 60) continue;
    fillPoly(ctx, boil(circlePts(62, y, 25, 28), sd(700 + h), 1, 30), GREY);
    inkLoop(ctx, circlePts(62, y, 25, 28), { seed: sd(710 + h), amp: 1.2, scale: 40, w: 4.5, color: CH, splits: 1 });
  }
}

function drawHeader(ta) {
  // tiny tracked tag
  const t0 = CUES.header.tag;
  const a = sstep(t0, t0 + 0.35, ta);
  if (a > 0) {
    const text = 'BEAT REPUBLIC MEDIA GROUP', track = 5.5;
    ctx.save();
    ctx.globalAlpha = a; ctx.fillStyle = CH; ctx.font = '600 24px "Montserrat"'; ctx.textBaseline = 'alphabetic';
    let x = 165 + (hs(V, 1) - 0.5) * 1.6; const y = RULE0 + RULE - 4 + (hs(V, 2) - 0.5) * 1.6;
    for (const ch of text) { ctx.fillText(ch, x, y); x += ctx.measureText(ch).width + track; }
    ctx.restore();
  }
  // hand-lettered title
  drawText({ fk: 'bagel', text: 'the list.', size: 150, x: 165, baseline: RULE0 + RULE * 4, t: ta, start: CUES.header.title - 0.04, stagger: 0.06, dur: 0.2, seed: 40, amp: 1.8, w: 3.4 });
}

// ------------------------------------------------------------------ closing line + contact
let CLOSE = null;
function closingLayout() {
  if (CLOSE) return CLOSE;
  const size0 = 112;
  const maxW = Math.max(...CUES.lines.map((l) => layout('bagel', l.text, size0).width));
  const size = Math.min(size0, Math.floor(size0 * 850 / maxW));
  const cx = (MARGIN_X + W) / 2;
  const kb = 36;   // first closing baseline on ruled line 36 (camera ends at y = 1900)
  CLOSE = { size, cx, base: CUES.lines.map((_, i) => RULE0 + RULE * (kb + i * 2)) };
  return CLOSE;
}
function drawClosing(ta) {
  const C = closingLayout();
  let lastW = 0, lastX0 = 0;
  CUES.lines.forEach((l, i) => {
    const r = drawText({ fk: 'bagel', text: l.text, size: C.size, x: C.cx, baseline: C.base[i], align: 'center', t: ta, start: l.start, stagger: 0.04, dur: 0.2, seed: 60 + i * 11, amp: 1.8, w: 3.4 });
    if (i === CUES.lines.length - 1) { lastW = r.width; lastX0 = r.x0; }
  });
  // red scribble under "music."
  const [u0] = CUES.underline;
  if (ta >= u0) {
    const y = C.base[CUES.lines.length - 1] + 40;
    const wv = (k) => (hs(k, 3) - 0.5) * 14;
    const A = [], n = 7;
    for (let k = 0; k <= n; k++) A.push([lerp(lastX0 - 10, lastX0 + lastW + 14, k / n), y + (k % 2 ? 7 : -7) + wv(k)]);
    stroke(A, { seed: sd(80), w: 13, color: RED, amp: 2.2, frac: inv(u0, u0 + 0.2, ta), t0: 8, t1: 16 });
    const B = [], m = 5;
    for (let k = 0; k <= m; k++) B.push([lerp(lastX0 + lastW * 0.82, lastX0 + lastW * 0.1, k / m), y + 26 + (k % 2 ? 5 : -5) + wv(k + 20)]);
    stroke(B, { seed: sd(81), w: 10, color: RED, amp: 2.2, frac: inv(u0 + 0.15, u0 + 0.35, ta), t0: 8, t1: 16 });
  }
  // contact, small tracked type
  const E = CUES.email;
  if (ta >= E.start) {
    const text = E.text, track = 7, sz = 28;
    ctx.save();
    ctx.fillStyle = CH; ctx.font = `600 ${sz}px "Montserrat"`; ctx.textBaseline = 'alphabetic';
    const ws = [...text].map((ch) => ctx.measureText(ch).width);
    const total = ws.reduce((a, b) => a + b, 0) + track * (text.length - 1);
    let x = C.cx - total / 2;
    const y = RULE0 + RULE * 46;
    [...text].forEach((ch, i) => {
      const a = clamp((ta - (E.start + i * 0.025)) / 0.12);
      if (a > 0) {
        ctx.globalAlpha = a;
        ctx.fillText(ch, x + (hs(V, i, 4) - 0.5) * 1.4, y + (hs(V, i, 5) - 0.5) * 1.4 + (1 - a) * 8);
      }
      x += ws[i] + track;
    });
    ctx.restore();
  }
}

// ------------------------------------------------------------------ frame
export function render(t) {
  const f = Math.round(t * FPS);
  V = Math.floor(f / 2) % 4;
  const ta = (Math.floor(f / 2) * 2) / FPS;          // animation time, on 2s

  // camera: on 1s (smooth) so motion blur can integrate it
  const [s0, s1] = CUES.slide;
  let camY = K(t, [[0, 0], [s0, 0], [s1, CUES.cam_y, 'io3'], [DURATION + 1, CUES.cam_y]]);
  camY += 4 * Math.sin(t * 2.1) * sstep(s1, s1 + 0.7, t);

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = PAPER; ctx.fillRect(0, 0, cv.width, cv.height);
  const sc = cv.width / W;
  ctx.setTransform(sc, 0, 0, sc, 0, -camY * sc);

  drawPage(camY);
  drawHeader(ta);
  for (let i = 0; i < CUES.rows.length; i++) {
    const y = ROW_BASE0 + ROW_PITCH * i;
    if (y < camY - 220 || y > camY + H + 220) continue;
    drawRow(i, ta);
  }
  if (camY + H > closingLayout().base[0] - 200) drawClosing(ta);

  // paper grain (multiply), scrolls with the page
  ctx.setTransform(sc, 0, 0, sc, 0, 0);
  ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = 0.9;
  const off = camY % H;
  ctx.drawImage(GRAIN, 0, -off); ctx.drawImage(GRAIN, 0, H - off);
  ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
}
