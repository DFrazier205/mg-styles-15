# CRANKINGTON — "DC Skyline Cut": score + sound design, locked to cues.json.
# City-night ambience bed -> pen whisper that follows the pen's speed (derived from the same piece timings the picture
# uses) -> breath of near-silence -> stick swish -> ONE synthesized conga hit on the cue -> soft A bass tone under the crest.
# (The repo's conga sample file is missing, so the hit is synthesized: pitched membrane + slap + shell resonance.)
import sys, json, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'audio'))
import mgaudio as mg
from mgaudio import sfx, synth, filters

HERE = os.path.dirname(os.path.abspath(__file__))
cues = json.load(open(os.path.join(HERE, 'cues.json')))
SR = 48000
N = int(10 * SR); tt = np.arange(N) / SR
HIT = cues['hit']; BREATH = cues['audio']['breath']; STK = cues['stick']
rng = np.random.default_rng(20261012)


def f32(x): return np.asarray(x, dtype=np.float32)
def noise(seed, n=N): return f32(np.random.default_rng(seed).standard_normal(n))
def bp(x, lo, hi): return filters.lpf(filters.hpf(f32(x), lo), hi)
def stereo(L, R): return mg.Sound(f32(np.stack([L, R])))
def env_at(pts):  # piecewise-linear dB-less gain envelope (linear amplitude) over the full 10 s
    return f32(np.interp(tt, [p[0] for p in pts], [p[1] for p in pts]))


# ---------------------------------------------------------------- pen speed from the picture's own timing
def ease_io(x):   # cubic-bezier(0.65,0,0.35,1) by bisection, as the picture does
    x = min(max(x, 0.0), 1.0)
    lo, hi = 0.0, 1.0
    bx = lambda u: 3 * (1 - u) ** 2 * u * 0.65 + 3 * (1 - u) * u * u * 0.35 + u ** 3
    by = lambda u: 3 * (1 - u) * u * u * 1.0 + u ** 3
    for _ in range(40):
        mid = (lo + hi) / 2
        if bx(mid) < x: lo = mid
        else: hi = mid
    return by((lo + hi) / 2)
def ease_out3(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def piece_ease(kind, x):
    if kind == 'out': return ease_out3(x)
    if kind == 'linear': return x
    if kind == 'mild': return 0.5 * x + 0.5 * ease_io(x)
    return ease_io(x)

TS = np.arange(0, 10, 1 / 240.0)
S = np.zeros_like(TS); cum = 0.0
for p in cues['pieces']:
    for i, t in enumerate(TS):
        if t >= p['t1']: S[i] = max(S[i], cum + p['len'])
        elif t > p['t0']: S[i] = cum + p['len'] * piece_ease(p['ease'], (t - p['t0']) / (p['t1'] - p['t0']))
    cum += p['len']
S = np.maximum.accumulate(S)
spd = np.gradient(S, TS)                                   # px / s, the pen
# the stick is drawn on at constant-ish speed in its own window
a, b = STK['draw']; spd[(TS >= a) & (TS < b)] = np.maximum(spd[(TS >= a) & (TS < b)], STK['length'] * 1.2 / (b - a))
spd_n = np.interp(tt, TS, spd)
pen_env = f32(np.clip(spd_n / 2200.0, 0, 1) ** 0.65)
pen_env = filters.lpf(pen_env, 28.0)
pen_env *= (tt < b + 0.03)                                  # the pen lifts when the stick is finished
grain = filters.lpf(noise(5), 60.0); grain = 1 + 0.9 * grain / (np.abs(grain).max() + 1e-9)
pen = stereo(bp(noise(1), 1500, 7500) * pen_env * grain, bp(noise(2), 1500, 7500) * pen_env * grain).loud(-18)

# ---------------------------------------------------------------- city-night ambience (never silent, ducks into the breath)
def lfo(rate, seed):
    x = filters.lpf(noise(seed), rate); return x / (np.abs(x).max() + 1e-9)
brown = filters.hpf(filters.lpf(noise(11), 220.0), 45.0)                       # low city rumble
road = bp(noise(12), 140, 900) * (0.55 + 0.45 * lfo(0.5, 13))          # distant traffic wash, slow swell
hiss = bp(noise(14), 3000, 9000) * 0.18 * (0.6 + 0.4 * lfo(0.8, 15))   # far-off air / HVAC
bed_L = brown * 1.0 + road * 0.8 + hiss; bed_R = filters.lpf(noise(16), 220.0) * 1.0 + bp(noise(17), 140, 900) * (0.55 + 0.45 * lfo(0.5, 18)) * 0.8 + bp(noise(19), 3000, 9000) * 0.12
amb = stereo(bed_L, bed_R).loud(-30)
# pass-by: two distant cars (doppler-ish sweeps), one siren-less hum
cars = [(1.7, 0.7, -0.5), (4.2, 0.9, 0.55)]
amb_gain = env_at([(0, 0.0), (0.3, 1.0), (BREATH[0] - 0.05, 1.0), (BREATH[0] + 0.12, 0.10), (HIT - 0.02, 0.10), (HIT + 0.02, 0.85),
                   (HIT + 1.2, 0.42), (9.4, 0.32), (10, 0.0)])
amb = mg.Sound(amb.data * amb_gain[None, :])

m = mg.Mix(duration=10.0, bpm=96)
m.group('music').level = -20
bed = m.track('city', level=-34, group='sfx', sends={'room': -22})
bed.add(amb, 0.0)
penT = m.track('pen', level=-27, group='sfx')
penT.add(pen, 0.0)
for t, d, pan in cars:
    m.sfx(sfx.whoosh(d + 0.5, 'soft', direction=0, peak=0.5, seed=int(t * 10)), at=t, gain=-24, pan=pan, verb=-12)

# frame 0: the nib touches down
m.sfx(sfx.pen('pen', 0.22, strokes=[(0.0, 0.18)], seed=11), at=0.0, gain=-9, pan=-0.2)
# the breath: stick swish into the strike (peak at the hit)
m.sfx(sfx.whoosh(0.28, 'swish', direction=1, peak=0.8, seed=21), at=HIT - 0.012, gain=-8, pan=0.35)


# ---------------------------------------------------------------- the conga hit (synth: open tone on the head)
def conga(t_len=1.1, f0=232.0, seed=3):
    n = int(t_len * SR); t = np.arange(n) / SR
    pitch = f0 * (1 + 0.55 * np.exp(-t / 0.018))                      # head tension drop
    ph = 2 * np.pi * np.cumsum(pitch) / SR
    body = np.sin(ph) * np.exp(-t / 0.20) + 0.38 * np.sin(1.58 * ph + 0.4) * np.exp(-t / 0.11) + 0.20 * np.sin(2.30 * ph + 1.1) * np.exp(-t / 0.07)
    shell = np.sin(2 * np.pi * 112 * t) * np.exp(-t / 0.16) * 0.55      # the shell's thump
    slap = bp(f32(np.random.default_rng(seed).standard_normal(n)), 1800, 6200) * np.exp(-t / 0.011) * 1.1
    click = np.zeros(n); click[:int(0.0015 * SR)] = 1.0
    click = filters.lpf(f32(click), 5000.0) * 0.8
    y = f32(body + shell + slap + click)
    y *= np.minimum(1, t / 0.0007)                                       # 0.7 ms attack, no DC click
    y = np.tanh(y * 1.25) / 1.25
    wid = f32(bp(np.random.default_rng(seed + 1).standard_normal(n), 400, 2400) * np.exp(-t / 0.05) * 0.05)
    return mg.Sound(f32(np.stack([y + wid, y - wid])))
hit = conga().loud(-14)
m.sfx(hit, at=HIT, gain=3.5, verb=-9)
# a second, much lighter copy through the hall = the ripple's tail (not a second hit)
m.sfx(conga(0.8, 232.0, 7).loud(-26), at=HIT + 0.001, gain=0, verb=-3, pan=0.0)

# ---------------------------------------------------------------- soft bass tone (A), blooms on the hit
bs = m.track('bass', level=-22, sends={'hall': -14}, group='music')
t0, t1 = cues['audio']['bass_tone']
bs.add(synth.bass('A1', (t1 - t0) + 0.3, 0.8, 'sub'), t0 + 0.01, gain=-12)
sine = np.sin(2 * np.pi * 110.0 * tt) * 0.5 + np.sin(2 * np.pi * 220.0 * tt) * 0.16 + np.sin(2 * np.pi * 164.8 * tt) * 0.08          # A2 + a whisper of the fifth
sine = sine * env_at([(0, 0), (HIT, 0), (HIT + 0.35, 1.0), (9.2, 0.8), (10, 0.0)])
bs.add(mg.Sound(f32(np.stack([sine, sine]))), 0.0, gain=-4)
bs.automate('gain', [(0, -60), (HIT - 0.01, -60), (HIT + 0.02, 0), (9.0, -1), (10, -14)])

# a faint breath of air once the crest has landed
m.sfx(sfx.sparkle(1.4, density=6, key='A', mode='minor_pentatonic', seed=8), at=8.55, gain=-24, verb=-8)

m.group('sfx').automate('gain', [(0, 0), (9.3, 0), (9.8, -4), (10, -14)])
m.master_kw.update(air=1.5)
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
res = m.export(os.path.join(HERE, 'out/audio.wav'), lufs=-14, tp=-1, spectrogram=os.path.join(HERE, 'out/audio_spec.png'))
print({k: res[k] for k in ('duration', 'lufs', 'true_peak', 'stereo_corr', 'longest_gap') if k in res})
print('bands', res.get('bands')); print('warnings', res.get('warnings'))
print('align', mg.hit_alignment(os.path.join(HERE, 'out/audio.wav'), [HIT]))
