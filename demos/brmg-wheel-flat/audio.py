"""BRMG "Show Day Wheel" — soundtrack (15 s, 120 bpm, a seamless loop).

Strictly the brief: each wheel turn lands on a SNARE (t = 0, 3, 6, 9, 12), the clock TICK is the HI-HAT (every 0.25 s,
60 per loop, the hand steps on each), a KICK on every beat, a CLAP on beats 2 and 4, and one pitched BLIP per scene
(C5 E5 G5 A5 C6, at each scene's hero moment). A short noise swell rides each turn into its snare.

Loop-safe: nothing rings across the loop point. The last hat is a 55 ms tick at 14.75, the last kick/clap decay by
14.9, the swell into the 15 s landing is wrapped (its tail lands at the start of the file, where the snare is), and
the file gets a 2 ms fade-in / 12 ms fade-out so the seam has no click.
"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'audio'))
import mgaudio as mg
from mgaudio import sfx, drums
from mgaudio.core import Sound, SR

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'cues.json')))
BPM, DUR = C['bpm'], float(C['duration'])
BEAT = 60 / BPM
TICK = C['tick']

m = mg.Mix(duration=DUR, bpm=BPM, anchor=0.0)
m.group('music').level = -18
m.sfx_duck = 0.0

tk = m.track('kick', level=-16)
tsn = m.track('snare', level=-19, sends={'room': -9})
tcl = m.track('clap', level=-18, sends={'room': -12}, pan=0.1)
tht = m.track('hat', level=-24, pan=0.2)

# kick on every beat
n_beats = int(round(DUR / BEAT))
for k in range(n_beats):
    tk.add(drums.kick('punchy', 0.95 if k % 4 == 0 else 0.82, decay=0.24), k * BEAT)
# clap on beats 2 and 4 of every bar (t = 0.5, 1.5, 2.5, ...)
for k in range(n_beats):
    if k % 2 == 1:
        tcl.add(drums.clap('tight', 0.8), k * BEAT)
# hi-hat = the clock tick, every 0.25 s (60 per loop); the off-beat 8ths a little brighter
for n in range(int(round(DUR / TICK))):
    t = n * TICK
    off = n % 2 == 1
    tht.add(drums.hat('closed', 0.78 if off else 0.58, decay=0.05), t)
# snare on every wheel landing
for L in C['turn']['landings']:
    tsn.add(drums.snare('tight', 1.0, decay=0.2), L)

# noise swell into each landing (wrapped for the 15 s == 0 s landing)
SW = 0.45
for L in C['turn']['landings']:
    w = sfx.whoosh(SW, 'swish', 1, 0.97, seed=int(L) + 5)
    start = L - SW * 0.97
    if start >= 0:
        m.sfx(w, at=start, gain=-6)
    else:
        # the head of the swell belongs at the end of the file, the tail at the start
        t0 = start + DUR
        n_head = int(round((DUR - t0) * SR))
        head = Sound(w.data[:, :n_head].copy()); tail = Sound(w.data[:, n_head:].copy())
        m.sfx(head, at=t0, gain=-6)
        m.sfx(tail, at=0.0, gain=-6)

# one pitched blip per scene, at its hero moment (a quiet echo 0.25 s later)
for s in C['slots']:
    t = s['land'] + s['hero']
    m.sfx(sfx.blip(s['note'], 'sine', dur=0.16, glide=2.0), at=t, gain=8, pan=0.15)
    m.sfx(sfx.blip(s['note'], 'sine', dur=0.12, glide=0.0), at=t + 0.25, gain=-6, pan=-0.2)

out = os.path.join(HERE, 'out')
os.makedirs(out, exist_ok=True)
res = m.export(os.path.join(out, 'audio.wav'), lufs=-14, tp=-1.05, spectrogram=os.path.join(out, 'audio_spec.png'))
m.report()

# seam: 2 ms fade-in, 12 ms fade-out (no click at the loop point), then re-check peak
import soundfile as sf
x, sr = sf.read(os.path.join(out, 'audio.wav'), always_2d=True)
fi, fo = int(0.002 * sr), int(0.012 * sr)
x[:fi] *= np.linspace(0, 1, fi)[:, None]
x[-fo:] *= np.linspace(1, 0, fo)[:, None]
info = sf.info(os.path.join(out, 'audio.wav'))
sf.write(os.path.join(out, 'audio.wav'), x, sr, subtype=info.subtype)
print({k: res[k] for k in ('duration', 'lufs', 'true_peak', 'warnings') if k in res})
print('first 2 ms rms', float(np.sqrt((x[:fi * 2] ** 2).mean())), 'last 12 ms rms', float(np.sqrt((x[-fo:] ** 2).mean())))
