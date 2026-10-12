"""Go-Go Royalty.com 'Vintage Station' soundtrack: VHS tape-on, outrun synthwave with a go-go conga groove under the drop.
Times come from cues.json (same file as the picture). 100 bpm, A minor."""
import sys, json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, ROOT + '/lib/audio')
import mgaudio as mg
from mgaudio import recipes, sfx, drums, samples, filters as F
from mgaudio.core import Sound
C = json.load(open(os.path.join(HERE, 'cues.json')))
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
SR = 48000
norm = lambda y, pk=.9: y * (pk / (np.max(np.abs(y)) + 1e-9))

m = recipes.synthwave(bpm=C['bpm'], key=C['key'], mode=C['mode'], drop=C['drop'], build=C['build'], outro=C['outro'], music_level=-23)
f = m.form
mus = m.group('music')
mus.region('filter', 0.0, C['track_lock'] + 0.15, hz=[(0.0, 700), (C['track_lock'], 2400), (C['track_lock'] + 0.15, 16000)], mode='lp')
S = m.sfx
DROP, OUT = C['drop'], C['outro']

# --- tape on: head noise, CRT, tracking lock
S(sfx.vhs_noise(1.35), at=0.0, gain=-3)
S(sfx.crt_on(), at=0.02, gain=-8)
S(sfx.static(0.9, 'tv'), at=0.05, gain=-13)
S(sfx.head_switch(), at=C['track_lock'], gain=-2)
for i, g in enumerate(C['glitches']):
    S(sfx.glitch(0.07, 'digital', seed=i), at=g, gain=-11 if g > DROP else -9)
S(sfx.riser(DROP - 1.6, 'noise', intensity=0.7), at=1.6, gain=-17)
S(sfx.vinyl(OUT - 1.0), at=0.9, gain=-26)                        # worn-tape / record crackle under the whole film

# --- the slam: chrome title
S(sfx.impact('cinematic'), at=DROP, gain=0, verb=-12)
S(sfx.boom(1.6), at=DROP, gain=-5)
S(sfx.shimmer_hit(f.chord_at(C['glint'][0])[-1] + 12), at=C['glint'][0], gain=-7, pan=-0.4)

# --- neon 1977-2009 write-on, flickers
S(sfx.charge(C['neon'][1] - C['neon'][0]), at=C['neon'][0], gain=-8, pan=0.25)
for a, b in C['neon_off']:
    S(sfx.zap(), at=b, gain=-8, pan=0.3)
    S(sfx.click('switch'), at=a - 1 / 60, gain=-6, pan=0.3)

# --- title leaves, sun slides, seal
S(sfx.whoosh(0.5, 'air', direction=1, peak=0.6, seed=3), at=C['title_exit'][0], gain=-7)
S(sfx.whoosh(0.8, 'heavy', direction=-1, peak=0.5, seed=4), at=C['sun_move'][0], gain=-10, pan=-0.3)
S(sfx.shimmer_hit(f.chord_at(C['seal'][0])[-1] + 12), at=C['seal'][0] + 0.1, gain=-8, pan=0.2)
S(sfx.sparkle(0.6, key=C['key'], mode=C['mode'], seed=2), at=C['seal'][0] + 0.15, gain=-13, pan=-0.2)

# --- end card lines and CTA
for i, t in enumerate(C['frags']):
    S(sfx.ui('swipe'), at=t, gain=-12)
    S(sfx.pop('soft', pitch=1.0 + 0.15 * i), at=t + 0.05, gain=-9)
S(sfx.pop('bubble', pitch=1.5), at=C['cta'] + 0.05, gain=-8)
S(sfx.chime(('E6', 'G6', 'B6', 'E7'), 0.07), at=C['cta'] + 0.1, gain=-14)
S(sfx.shimmer_hit(f.chord_at(OUT)[-1] + 12), at=OUT, gain=-10, pan=0.3)
S(sfx.sparkle(0.5, key=C['key'], mode=C['mode'], seed=5), at=OUT + 0.2, gain=-15, pan=-0.3)
mar = samples.inst('marimba')
btn = m.track('button', level=-25, sends={'hall': -12})
btn.add(mar.play('A4', dur=0.6, vel=0.6), OUT + 0.05); btn.add(mar.play('E5', dur=1.0, vel=0.65), OUT + 0.2)


# --- go-go conga groove under the drop (conga synth from One Drop)
def conga(kind='open', vel=0.9, seed=0):
    r = np.random.default_rng(seed); n = int(0.6 * SR); t = np.arange(n) / SR
    f0 = {'open': 205, 'low': 150, 'slap': 255, 'mute': 225}[kind]; tau = {'open': 0.17, 'low': 0.24, 'slap': 0.05, 'mute': 0.045}[kind]
    fq = f0 * (1 + 0.38 * np.exp(-t / 0.02)); ph = 2 * np.pi * np.cumsum(fq) / SR
    tone = np.sin(ph) * np.exp(-t / tau) + 0.33 * np.sin(ph * 1.52 + 0.7) * np.exp(-t / (tau * 0.4)) + 0.12 * np.sin(ph * 2.3) * np.exp(-t / (tau * 0.25))
    nz = F.bpf(r.standard_normal(n), 900, 3600) * np.exp(-t / {'open': 0.014, 'slap': 0.032, 'low': 0.014, 'mute': 0.01}[kind])
    y = tone * 0.85 + nz * {'slap': 0.95, 'open': 0.38, 'low': 0.3, 'mute': 0.3}[kind]
    y = F.lpf(y, 5500); y = y / (np.max(np.abs(y)) + 1e-9) * vel
    return Sound(np.stack([y, y]).astype(np.float32), 0.0)

cg = m.track('conga', level=-15, sends={'room': -14})
rm = m.track('rim', level=-28, sends={'room': -12}, group='music')
cb = m.track('cowbell', level=-28, pan=0.3, group='music')
kinds = ['low', 'open', 'slap', 'open', 'slap', 'low', 'open', 'slap']
step = 60 / C['bpm'] / 4
pat = 'x.xx.x..x.xx.x.x'
for j in range(-8, int((OUT - DROP) / step) + 1):            # 8-step pre-roll into the drop (matches the picture's groove())
    t = DROP + j * step
    if t >= OUT - 0.02: break
    bar, k = divmod(j, 16)
    if pat[k] == 'x': cg.add(conga(kinds[(bar * 3 + k) % 8], (0.95 if k % 4 == 0 else 0.8) * (0.55 if j < 0 else 1.0), seed=k + 7 * (bar % 10)), t)
rm.loop(lambda v: drums.rim(v), '....x.......x...', DROP, OUT)
cb.loop(lambda v: drums.cowbell(v), 'x..x..x...x.x...', DROP, OUT)

hits = [C['track_lock'], DROP, C['neon'][0], C['seal'][0], C['cta'], OUT]
res = m.export(os.path.join(HERE, 'out/audio.wav'), lufs=-14, tp=-2.0, spectrogram=os.path.join(HERE, 'out/audio_spec.png'))
import soundfile as _sf
from scipy.signal import butter as _bt, sosfiltfilt as _sff
_x, _sr = _sf.read(os.path.join(HERE, 'out/audio.wav')); _sf.write(os.path.join(HERE, 'out/audio.wav'), _sff(_bt(4, 16000, 'low', fs=_sr, output='sos'), _x, axis=0), _sr, subtype='PCM_24')
print({k: res[k] for k in ('duration', 'lufs', 'true_peak', 'stereo_corr', 'warnings') if k in res})
print('align', mg.hit_alignment(os.path.join(HERE, 'out/audio.wav'), hits))
