"""Fluid stadium assembly: soundtrack (mgaudio). Every event time is read from cues.json, the same file the picture reads.
Arc: sub hum + tension ticks -> magnetic split (1.5 s) -> rolling ASMR rain of landing clicks (2.4-7.0 s) -> final lock,
distant gong and wind through the canopy (7.0 s) -> stillness. Key: D."""
import sys, json, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'audio'))
import numpy as np
import mgaudio as mg
from mgaudio import synth, drums, sfx
from mgaudio.theory import midi

HERE = os.path.dirname(os.path.abspath(__file__))
cues = json.load(open(os.path.join(HERE, 'cues.json')))
N = lambda s: midi(s) if isinstance(s, str) else s
R = np.random.default_rng(2026)

m = mg.Mix(10.0, bpm=cues['bpm'], anchor=cues['final'])
m.group('music').level = -20

# ---------------------------------------------------------------- geometry helpers (pan follows the piece on screen)
RX, RY, PW = 100.0, 70.0, 2 / 2.6
def E(rho, phi):
    c, s = math.cos(phi), math.sin(phi)
    return RX * rho * math.copysign(abs(c) ** PW, c), RY * rho * math.copysign(abs(s) ** PW, s)
def pan_of(X, Y):
    return float(np.clip((X - Y) * 0.866 * 5.4 / 780.0, -0.7, 0.7))
NSEG = cues['nseg']; dphi = 2 * math.pi / NSEG
TIER_RHO = [0.62, 0.765, 0.91]

# ---------------------------------------------------------------- 0.0-1.5 : the container hums, tension ticks
hum = m.track('hum', level=-24, sends={'hall': -12})
hum.add(synth.bass(N('D2'), 1.9, 0.8, 'sub'), 0.0)
hum.add(synth.bass(N('D1'), 1.9, 0.7, 'sub'), 0.0)
hum.automate('gain', [(0.0, -14), (0.6, -6), (1.4, 0), (1.55, 0), (1.9, -10), (2.4, -10)])
hum.automate('lpf', [(0.0, 300), (1.4, 1400), (1.6, 700)])
# metallic tension ticks: accelerating
tk = m.track('ticks', level=-30, pan=0.25, sends={'room': -14})
t, gap, g = 0.12, 0.30, 0
while t < 1.42:
    tk.add(sfx.tick('clock' if g % 2 == 0 else 'hi', level=-24), t)
    t += gap; gap = max(0.055, gap * 0.82); g += 1
# concrete tiles dropping in as a wave from the centre
for k, tr in enumerate(cues['rings']):
    m.sfx(sfx.click('wood'), at=tr + 0.2 - 1 / 30, gain=-19 + 0.2 * k, pan=-0.3 + 0.05 * k)
    if k % 3 == 0:
        m.sfx(sfx.impact('thud', size=0.25), at=tr + 0.2, gain=-26)
# scaffolding poles rising: soft ticks
for i in range(0, 32, 3):
    t0 = cues['scaffold']['start'] + (i / 32) * (cues['scaffold']['end'] - cues['scaffold']['start'])
    m.sfx(sfx.tick('wood'), at=t0 + 0.15, gain=-24, pan=-0.6 + 1.2 * (i / 32))

# ---------------------------------------------------------------- 1.15-1.5 : seams glow, then the magnetic release
m.sfx(sfx.charge(0.4), at=cues['seam'] - 0.02, gain=-15)
S = cues['split']
m.sfx(sfx.click('switch'), at=S - 0.012, gain=-5)
m.sfx(sfx.impact('soft', size=0.7), at=S, gain=-6)
m.sfx(sfx.sub_drop(0.7, 96, 38), at=S, gain=-9)
m.sfx(sfx.whoosh(0.8, 'air', direction=-1, peak=0.12, seed=4), at=S + 0.02, gain=-8)
m.sfx(sfx.shimmer_hit('D6'), at=S + 0.04, gain=-13)
# the lid halves slide apart
m.sfx(sfx.whoosh(0.5, 'soft', direction=1, peak=0.4, seed=5), at=S + 0.05, gain=-14, pan=0.2)
m.sfx(sfx.whoosh(0.5, 'soft', direction=-1, peak=0.4, seed=6), at=S + 0.07, gain=-14, pan=-0.2)

# ---------------------------------------------------------------- 2.4-7.0 : hyperlapse assembly, ASMR clicks
# field unfurls like fabric
m.sfx(sfx.whoosh(1.1, 'cloth', direction=1, peak=0.55, seed=7), at=cues['field']['start'], gain=-11, pan=0.0)
m.sfx(sfx.paper('slide', 0.9, seed=3), at=cues['field']['start'] + 0.1, gain=-19)
# a swelling air bed under the whole build
m.track('air', level=-30, sends={'hall': -10}).add(sfx.riser(4.6, 'noise', seed=2), 7.0 - 0.0)
# petals: each landing = a magnetic click (+ low tock on every 3rd); tier starts get a sliding whoosh
kinds = ['switch', 'hard', 'wood', 'soft']
for k, T in enumerate(cues['tiers']):
    first = min(T['spawn'])
    m.sfx(sfx.whoosh(0.7, 'soft', direction=1 if k % 2 == 0 else -1, peak=0.35, seed=10 + k), at=first + 0.05, gain=-15)
    for i, sp in enumerate(T['spawn']):
        land = sp + T['flight']
        phi = (i + 0.5 * (k % 2)) * dphi
        X, Y = E(TIER_RHO[k], phi)
        kd = kinds[int(R.integers(0, len(kinds)))]
        gn = -19 - 1.5 * R.random() - (1.5 if k == 0 else 0)
        m.sfx(sfx.click(kd), at=land - 1 / 30, gain=gn, pan=pan_of(X, Y))
        if i % 3 == 0:
            m.sfx(sfx.tick('tock'), at=land - 1 / 30, gain=-27, pan=pan_of(X, Y))
# trusses twist upward: expanding resin creaks
for i, sp in enumerate(cues['trusses']['spawn']):
    phi = (i + 0.25) * 2 * math.pi / 12
    X, Y = E(1.0, phi)
    m.sfx(sfx.stretch(0.7, up=True), at=sp + 0.05, gain=-21, pan=pan_of(X, Y))
# glass facade panels: tiny glassy ticks along the wave
for i, sp in enumerate(cues['facade']['spawn']):
    a = (i + 0.5) * dphi
    X, Y = E(0.995, a)
    if i % 2 == 0:
        m.sfx(sfx.tick('hi'), at=sp + 0.08, gain=-27, pan=pan_of(X, Y))
# ramps hang in suspension: airy whoosh + a soft thrum
for r, sp in enumerate(cues['ramps']['spawn']):
    m.sfx(sfx.whoosh(0.9, 'air', direction=-1 if r % 2 else 1, peak=0.4, seed=30 + r), at=sp, gain=-16, pan=[0.5, -0.5, -0.3, 0.3][r])
# pathways bloom like roots: rustle
for i, sp in enumerate(cues['roots']['spawn']):
    if i % 2 == 0:
        m.sfx(sfx.paper('rustle', 0.5, seed=40 + i), at=sp, gain=-28)

# ---------------------------------------------------------------- 5.4-7.0 : roof panels lock, tension rises into the hero beat
m.track('riser', level=-24, sends={'hall': -12}).add(sfx.riser(1.6, 'tonal', note='D3', seed=3), cues['final'])
roof = cues['roof']
for i, land in enumerate(roof['land']):
    phi = i * dphi
    X, Y = E(0.96, phi)
    last = (i == roof['final_index'])
    m.sfx(sfx.click('switch'), at=land - 1 / 30, gain=-17 if not last else -9, pan=pan_of(X, Y))
    m.sfx(sfx.tick('hi'), at=land - 1 / 30, gain=-22 - (0 if last else 2), pan=pan_of(X, Y))
for i in range(0, NSEG, 4):
    m.sfx(sfx.whoosh(0.5, 'sci', direction=1, peak=0.5, seed=60 + i), at=roof['spawn'][i] + 0.05, gain=-23)
# the halo ring forms and locks
H = cues['halo']
m.sfx(sfx.hud_scan(H['end'] - H['start'], 1), at=H['start'], gain=-15)
m.sfx(sfx.lock_on(0.5, note='D6'), at=H['end'] - 0.05, gain=-13)

# ---------------------------------------------------------------- 7.0 : the last panel closes the roof, light pours in
F = cues['final']
m.sfx(sfx.impact('soft', size=0.9), at=F, gain=-4)
m.sfx(sfx.impact('metal', size=0.5), at=F, gain=-12)
m.sfx(sfx.sub_drop(1.0, 80, 36), at=F, gain=-8)
m.sfx(sfx.shimmer_hit('D6'), at=F + 0.02, gain=-9)
m.sfx(sfx.magic(1.2, 'D', 'major_pentatonic', up=True, seed=6), at=F + 0.05, gain=-13)
# distant gong
g = m.track('gong', level=-22, sends={'hall': -6, 'plate': -10})
g.add(drums.gong('tamtam', 0.85, tune=-2.0), F + 0.02)
g.add(drums.gong('small', 0.5), F + 0.05)
# wind rushing gently through the open canopies, then stillness
m.sfx(sfx.whoosh(2.6, 'air', direction=0, peak=0.30, seed=11), at=F + 0.1, gain=-9)
m.sfx(sfx.whoosh(2.9, 'soft', direction=1, peak=0.5, seed=12), at=F + 0.2, gain=-11, pan=0.2)
m.sfx(sfx.whoosh(2.8, 'soft', direction=-1, peak=0.45, seed=13), at=F + 0.35, gain=-12, pan=-0.2)
m.sfx(sfx.sparkle(2.0, 9, 'D', 'major_pentatonic', seed=5), at=F + 0.4, gain=-24)
pad = m.track('pad', level=-26, sends={'hall': -8}, width=1.0)
pad.add(synth.pad([N('D3'), N('A3'), N('D4'), N('F#4'), N('A4')], 3.4, 0.7, 'glass'), F - 0.05)
pad.automate('lpf', [(6.9, 1200), (7.2, 5200), (8.8, 3000), (10.0, 1800)])
pad.automate('gain', [(6.9, -10), (7.3, 0), (8.6, -2), (9.9, -14)])
sub = m.track('sub', level=-26)
sub.add(synth.bass(N('D2'), 3.0, 0.7, 'sub'), F)
sub.automate('gain', [(7.0, 0), (9.0, -4), (10.0, -18)])

# ---------------------------------------------------------------- master
m.group('music').automate('gain', [(0, -2), (1.4, -1), (2.4, 0), (6.8, 0), (6.9, -9), (6.99, -9), (7.03, 1.5), (8.6, 0), (9.8, -3), (10.0, -6)])
m.master_kw.update(air=0.6)
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
wav = os.path.join(HERE, 'out', 'audio.wav')
res = m.export(wav, spectrogram=os.path.join(HERE, 'out', 'audio_spec.png'))
m.report()
print({k: res[k] for k in ('duration', 'lufs', 'true_peak', 'bands', 'warnings') if k in res})
first_lands = [min(T['spawn']) + T['flight'] for T in cues['tiers']]
hits = [cues['split'], cues['final']] + first_lands
print(mg.hit_alignment(wav, hits))
