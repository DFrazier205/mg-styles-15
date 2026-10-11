"""BRMG 'Built By Hand' soundtrack: brushy percussion, pencil scratches, a synthesized conga hit on every ink splash.

All times come from cues.json (same file the picture reads). 96 bpm, bar 0 anchored at the first splash (3.0 s).
Form: pencil drawing (0-3 s, light shaker) -> conga hits + brush groove (3-6.9 s) -> collapse whoosh (6.9 s) ->
three stamped word hits (7.2 / 7.5 / 7.8) -> pencil tagline + red underline -> soft marimba button.
"""
import sys, os, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib', 'audio'))
import mgaudio as mg
from mgaudio import sfx, drums, samples, filters as F
from mgaudio.core import Sound

SR = 48000
C = json.load(open(os.path.join(HERE, 'cues.json')))
BPM, ANCHOR = C['bpm'], C['anchor']


def conga(kind='open', vel=0.9, seed=0):
    """Synthesized conga: pitch-dropping skin tone + inharmonic overtone + hand-slap noise burst."""
    r = np.random.default_rng(seed)
    dur = 0.6
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = {'open': 205, 'low': 150, 'slap': 255, 'mute': 225}[kind]
    tau = {'open': 0.17, 'low': 0.24, 'slap': 0.05, 'mute': 0.045}[kind]
    f = f0 * (1 + 0.38 * np.exp(-t / 0.02))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) * np.exp(-t / tau) + 0.33 * np.sin(ph * 1.52 + 0.7) * np.exp(-t / (tau * 0.4)) + 0.12 * np.sin(ph * 2.3) * np.exp(-t / (tau * 0.25))
    nz = F.bpf(r.standard_normal(n), 900, 3600) * np.exp(-t / {'open': 0.014, 'slap': 0.032, 'low': 0.014, 'mute': 0.01}[kind])
    y = tone * 0.85 + nz * {'slap': 0.95, 'open': 0.38, 'low': 0.3, 'mute': 0.3}[kind]
    y = F.lpf(y, 5500)
    y = y / (np.max(np.abs(y)) + 1e-9) * vel
    return Sound(np.stack([y, y]).astype(np.float32), 0.0)


m = mg.Mix(duration=10.0, bpm=BPM, anchor=ANCHOR)
m.group('music').level = -20

# --- conga: one hit on every splash (picture reads the same times) -----------------------------------------
kinds = ['low', 'open', 'slap', 'open', 'slap', 'low', 'open', 'slap', 'open', 'low']
vels = [1.0, 0.85, 0.95, 0.8, 0.95, 0.9, 0.85, 0.95, 0.8, 1.0]
cg = m.track('conga', level=-17, sends={'room': -14})
for i, t in enumerate(C['hits']):
    cg.add(conga(kinds[i], vels[i], seed=10 + i), t)
# the three stamped wordmark hits (low congas)
for t, v in zip([C['words']['beat'], C['words']['republic'], C['words']['media']], [1.0, 0.85, 0.85]):
    cg.add(conga('low', v, seed=int(t * 10)), t)

# --- brushy percussion ---------------------------------------------------------------------------------------
brush = m.track('brush', level=-25, sends={'room': -12})
brush.loop(lambda v: drums.snare('brush', v), '....x.......x...', ANCHOR, C['collapse'][0])
shaker = m.track('shaker', level=-31, pan=0.2)
shaker.loop(lambda v: drums.shaker(v, 0.09), 'x.g.x.g.x.g.x.g.', 1.9, ANCHOR)
shaker.loop(lambda v: drums.shaker(v, 0.09), 'x.xgx.xgx.xgx.xg', ANCHOR, C['collapse'][0])
swirl = m.track('swirl', level=-33)
for i, t in enumerate(np.arange(ANCHOR, C['collapse'][0], 60 / BPM)):
    swirl.add(sfx.swish(0.3, direction=1 if i % 2 == 0 else -1, seed=i), float(t) + 0.12)

# --- pencil / marker drawing ---------------------------------------------------------------------------------
m.sfx(sfx.pen('pencil', 0.6, seed=1), at=C['ground'][0], gain=-2)
m.sfx(sfx.pen('pencil', 2.1, seed=2), at=C['desk'][0] + 0.1, gain=-3)
m.sfx(sfx.pen('pencil', 0.95, seed=3), at=C['mic'][0], gain=-3)
m.sfx(sfx.pen('pencil', 0.95, seed=4), at=C['conga'][0], gain=-3)
m.sfx(sfx.pen('marker', 0.55, seed=5), at=2.25, gain=-6)
m.sfx(sfx.pen('pencil', C['tagline'][1] - C['tagline'][0], seed=6), at=C['tagline'][0], gain=-3)
m.sfx(sfx.pen('marker', C['underline'][1] - C['underline'][0], seed=7), at=C['underline'][0], gain=-3)

# --- cel smoke + speed lines ---------------------------------------------------------------------------------
for i, t in enumerate(C['smoke']):
    m.sfx(sfx.whoosh(0.75, 'soft', direction=0, peak=0.4, seed=20 + i), at=t + 0.3, gain=-7)
for i, t in enumerate(C['speed']):
    m.sfx(sfx.swish(0.28, direction=1 if i % 2 == 0 else -1, seed=30 + i), at=t + 0.1, gain=-3)

# --- ink splashes on each conga hit --------------------------------------------------------------------------
for i, t in enumerate(C['hits']):
    m.sfx(sfx.splash(0.3, seed=40 + i), at=t, gain=-10)

# --- collapse into the wordmark -------------------------------------------------------------------------------
m.sfx(sfx.whoosh(0.8, 'heavy', direction=-1, peak=0.75, seed=50), at=C['collapse'][0] + 0.35, gain=-2)
for t, g in zip([C['words']['beat'], C['words']['republic'], C['words']['media']], [-1, -3, -3]):
    m.sfx(sfx.stamp('rubber', seed=int(t * 10)), at=t, gain=g)

# --- soft marimba button on the end frame ---------------------------------------------------------------------
mar = samples.inst('marimba')
btn = m.track('button', level=-27, sends={'hall': -12})
btn.add(mar.play('G4', dur=0.5, vel=0.55), 9.5)
btn.add(mar.play('D5', dur=0.9, vel=0.5), 9.6)

if __name__ == '__main__':
    out = os.path.join(HERE, 'out')
    os.makedirs(out, exist_ok=True)
    res = m.export(os.path.join(out, 'audio.wav'), spectrogram=os.path.join(out, 'audio_spec.png'))
    m.report()
    print({k: res[k] for k in ('duration', 'lufs', 'true_peak', 'sample_peak', 'stereo_corr', 'warnings') if k in res})
