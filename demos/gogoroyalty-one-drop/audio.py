"""Go-Go Royalty.com 'One Drop' soundtrack: deep drip, rising liquid swell, a go-go conga groove kicking in at the split.
Times come from cues.json (same file as the picture). 100 bpm, bar grid anchored at the split (3.6 s)."""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib', 'audio'))
import mgaudio as mg
from mgaudio import sfx, drums, samples, synth, filters as F
from mgaudio.core import Sound

SR = 48000
C = json.load(open(os.path.join(HERE, 'cues.json')))
BPM, SPLIT, IMP = C['bpm'], C['split'], C['impact']
END_GROOVE = C['wash'][0] + 0.6
m = mg.Mix(duration=10.0, bpm=BPM, anchor=SPLIT)
m.group('music').level = -20


def conga(kind='open', vel=0.9, seed=0):
    r = np.random.default_rng(seed); n = int(0.6 * SR); t = np.arange(n) / SR
    f0 = {'open': 205, 'low': 150, 'slap': 255, 'mute': 225}[kind]; tau = {'open': 0.17, 'low': 0.24, 'slap': 0.05, 'mute': 0.045}[kind]
    f = f0 * (1 + 0.38 * np.exp(-t / 0.02)); ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) * np.exp(-t / tau) + 0.33 * np.sin(ph * 1.52 + 0.7) * np.exp(-t / (tau * 0.4)) + 0.12 * np.sin(ph * 2.3) * np.exp(-t / (tau * 0.25))
    nz = F.bpf(r.standard_normal(n), 900, 3600) * np.exp(-t / {'open': 0.014, 'slap': 0.032, 'low': 0.014, 'mute': 0.01}[kind])
    y = tone * 0.85 + nz * {'slap': 0.95, 'open': 0.38, 'low': 0.3, 'mute': 0.3}[kind]
    y = F.lpf(y, 5500); y = y / (np.max(np.abs(y)) + 1e-9) * vel
    return Sound(np.stack([y, y]).astype(np.float32), 0.0)


# --- act 1: the drop (no groove yet): a low tension hum while the bead grows, bead tick, deep drip on impact, ripples, rising swell
m.sfx(sfx.riser(2.0, 'hybrid', note='C2', intensity=0.6), at=0.2, gain=-14)
m.sfx(sfx.bubbles(1.2, density=6.0, seed=1), at=0.6, gain=-20)
m.sfx(sfx.drip(pitch=1.7), at=1.1, gain=-20)
m.sfx(sfx.drip(pitch=1.4), at=C['fall'] - 0.05, gain=-14)
m.sfx(sfx.drip(pitch=0.55), at=IMP - 0.01, gain=-3)
m.sfx(sfx.sub_drop(0.9, 90.0, 34.0), at=IMP, gain=-8)
m.sfx(sfx.splash(0.9, seed=2), at=IMP + 0.02, gain=-14)
m.sfx(sfx.bubbles(1.4, density=14.0, seed=3), at=IMP + 0.3, gain=-18)
m.sfx(sfx.riser(1.3, 'noise', intensity=0.8), at=IMP + 0.1, gain=-16)
m.sfx(sfx.gloop(pitch=0.8), at=SPLIT - 0.04, gain=-6)
m.sfx(sfx.gloop(pitch=1.1), at=SPLIT + 0.25, gain=-9)

# --- act 2: the groove "kicks in" at the split; each station label adds a layer (4.2 / 4.8 / 5.4)
cg = m.track('conga', level=-17, sends={'room': -14}); kk = m.track('kick', level=-20, group='music'); rm = m.track('rim', level=-26, sends={'room': -12}, group='music')
cb = m.track('cowbell', level=-30, pan=0.3, group='music'); hh = m.track('hat', level=-32, pan=-0.2, group='music'); bs = m.track('bass', level=-22, group='music')
L = C['labels']; T_V, T_T, T_B = L[0][2], L[1][2], L[2][2]
kinds = ['low', 'open', 'slap', 'open', 'slap', 'low', 'open', 'slap']
def congas(t0, t1):
    pat = 'x.xx.x..x.xx.x.x'                                  # go-go conga phrase on 16ths
    step = 60 / BPM / 4; i = 0
    for bar in range(40):
        for k, ch in enumerate(pat):
            t = t0 + bar * 16 * step + k * step
            if t >= t1: return
            if ch == 'x': cg.add(conga(kinds[(bar * 3 + k) % 8], 0.95 if k % 4 == 0 else 0.8, seed=k + 7 * bar), t)
congas(SPLIT, END_GROOVE)
rm.loop(lambda v: drums.rim(v), '....x.......x...', T_V - 0.0, END_GROOVE)       # Vintage: rim on the backbeat
cb.loop(lambda v: drums.cowbell(v), 'x..x..x...x.x...', T_V, END_GROOVE)
hh.loop(lambda v: drums.hat('closed', v), 'x.xxx.xxx.xxx.xx', T_T, END_GROOVE)    # Today's: hats
kk.loop(lambda v: drums.kick('punchy', v), 'x.....x.x.x.....', T_B, END_GROOVE)    # BounceBeat: kick bounce
bs.loop(lambda v: synth.b808('C2', 0.26, v), 'x.....x.x.......', T_B, END_GROOVE)
# station label pops, climbing
for i, (nm, yrs, t) in enumerate(L):
    m.sfx(sfx.pop('bubble', pitch=1.0 + 0.2 * i), at=t + 0.25, gain=-7)

# --- act 3: the pour into the wordmark (three streams), letters filling, wash to white and the puddle
for i, t0 in enumerate([C['pour'][0] + 0.05, C['pour'][0] + 0.15, C['pour'][0] + 0.25]):
    m.sfx(sfx.whoosh(0.7, 'swoosh', direction=1, peak=0.5, seed=10 + i), at=t0, gain=-10, pan=[-0.4, 0, 0.4][i])
m.sfx(sfx.riser(1.8, 'hybrid', note='C3', intensity=1.0), at=C['pour'][0] + 0.3, gain=-14)
m.sfx(sfx.bubbles(1.6, density=24.0, seed=5), at=C['pour'][0] + 0.8, gain=-16)
m.sfx(sfx.splash(1.2, seed=6), at=C['wash'][0] - 0.02, gain=-8)
m.sfx(sfx.sub_drop(0.8, 120.0, 40.0), at=C['wash'][0], gain=-10)
for i in range(6): m.sfx(sfx.drip(pitch=1.0 + 0.1 * i), at=C['wash'][0] + 0.2 + 0.06 * i, gain=-14 - i)

# --- ending: 'Free, 24/7' pop, CTA chime and marimba button
mar = samples.inst('marimba')
m.sfx(sfx.pop('soft', pitch=1.2), at=C['line'] + 0.15, gain=-7)
m.sfx(sfx.pop('bubble', pitch=1.5), at=C['cta'] + 0.2, gain=-7)
m.sfx(sfx.chime(('E6', 'G6', 'B6', 'E7'), 0.07), at=C['cta'] + 0.25, gain=-14)
btn = m.track('button', level=-24, sends={'hall': -12})
btn.add(mar.play('G4', dur=0.6, vel=0.6), 9.0); btn.add(mar.play('D5', dur=1.2, vel=0.65), 9.15)

if __name__ == '__main__':
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    res = m.export(os.path.join(out, 'audio.wav'), spectrogram=os.path.join(out, 'audio_spec.png'))
    m.report()
    print({k: res[k] for k in ('duration', 'lufs', 'true_peak', 'sample_peak', 'stereo_corr', 'warnings') if k in res})
