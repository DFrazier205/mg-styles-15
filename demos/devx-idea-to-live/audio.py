"""DevX 'From Idea to Live' soundtrack: upbeat claps and pops, pitch rising on every step. Times come from cues.json (same file as the picture)."""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib', 'audio'))
import mgaudio as mg
from mgaudio import sfx, drums, samples

C = json.load(open(os.path.join(HERE, 'cues.json')))
BPM = C['bpm']; HF = C['highfives']; M = C['morphs']; SP = C['split']
m = mg.Mix(duration=10.0, bpm=BPM, anchor=0.0)
m.group('music').level = -20
mar = samples.inst('marimba')
RISE = ['C5', 'D5', 'E5', 'G5', 'A5']            # one step up per high-five
PITCH = [1.0, 1.12, 1.26, 1.5, 1.68]

# --- backing groove: soft kick on every beat, offbeat hats, clap on 2 & 4 (beats = 0.5 s)
kk = m.track('kick', level=-22, group='music'); hh = m.track('hat', level=-32, pan=0.25, group='music'); cl = m.track('clap', level=-26, sends={'room': -14}, group='music')
for b in range(int(0.5 / 0.5), 16):
    t = b * 0.5
    if 0.5 <= t < 8.0:
        kk.add(drums.kick('punchy', 0.8), t)
        hh.add(drums.hat('closed', 0.6), t + 0.25)
        if b % 2 == 0: cl.add(drums.clap('tight', 0.8), t)
# --- bouncy marimba bass-ish pulse
bs = m.track('bass', level=-27, sends={'room': -12}, group='music')
for i, n in enumerate(['C3', 'C3', 'G3', 'A3'] * 4):
    t = 0.5 + i * 0.5
    if t < 8.0: bs.add(mar.play(n, dur=0.4, vel=0.6), t + 0.25)

# --- high-fives: real clap + pop, rising pitch; marimba note on each step
hf = m.track('hf', level=-14, sends={'room': -14})
for i, t in enumerate(HF):
    hf.add(drums.clap('808', 1.0), t)
    m.sfx(sfx.pop('bubble', pitch=PITCH[i]), at=t, gain=-4)
    m.sfx(sfx.sparkle(0.5, density=22.0, seed=70 + i), at=t + 0.02, gain=-14)
    hf.add(mar.play(RISE[i], dur=0.6, vel=0.85), t)
    hf.add(mar.play(RISE[i].replace('5', '6'), dur=0.5, vel=0.55), t + 0.25)

# --- bulb drop + light-on
m.sfx(sfx.whoosh(0.5, 'swoosh', direction=-1, peak=0.5, seed=1), at=C['bulbDrop'] - 0.02, gain=-8)
m.sfx(sfx.pop('soft', pitch=0.8), at=C['bulbDrop'] + 0.45, gain=-4)
m.sfx(sfx.toggle(True), at=C['bulbOn'] - 0.02, gain=-6)
m.sfx(sfx.ding('E6', 'bell', 0.9), at=C['bulbOn'] + 0.02, gain=-14)

# --- title cards drop in with a thunk + pop
for i, (lab, t) in enumerate(C['titles']):
    m.sfx(sfx.swish(0.3, direction=-1, seed=10 + i), at=t - 0.05, gain=-8)
    m.sfx(sfx.pop('mouth', pitch=0.9 + 0.12 * i), at=t + 0.3, gain=-6)

# --- morphs: bulb -> sketch -> wireframe -> site, each a notch higher
for i, k in enumerate(['sketch', 'wire', 'site']):
    t = M[k]
    m.sfx(sfx.morph(0.45, True, ['A3', 'C4', 'E4'][i]), at=t - 0.05, gain=-12)
    m.sfx(sfx.pop('bubble', pitch=1.1 + 0.15 * i), at=t + 0.3, gain=-9)
m.sfx(sfx.pen('pencil', 1.0, seed=3), at=M['sketch'] + 0.3, gain=-8)          # pencil strokes of the sketch
m.sfx(sfx.sticker_slap(seed=4), at=M['site'] + 0.1, gain=-12)
for j in range(8):                                                           # site blocks pop in, ascending
    m.sfx(sfx.pop('soft', pitch=1.0 + 0.07 * j), at=M['site'] + 0.2 + j * 0.11, gain=-18)

# --- split: app icon + AI chat bubble fly out
m.sfx(sfx.whoosh(0.6, 'swoosh', direction=1, peak=0.6, seed=5), at=SP['start'] - 0.02, gain=-9)
m.sfx(sfx.pop('cork'), at=SP['app'] + 0.25, gain=-6)
m.sfx(sfx.pop('bubble', pitch=1.7), at=SP['app'] + 0.3, gain=-8)
m.sfx(sfx.pop('cork', pitch=1.2) if False else sfx.pop('bubble', pitch=1.9), at=SP['chat'] + 0.3, gain=-6)
m.sfx(sfx.chime(('C6', 'E6', 'G6', 'C7'), 0.06), at=SP['chat'] + 0.35, gain=-14)

# --- closing line: a pop per word, climbing, and a soft button
ln = C['line']
for i in range(8):
    m.sfx(sfx.pop('soft', pitch=0.9 + 0.06 * i), at=ln['start'] + i * ln['stagger'] + 0.05, gain=-15)
m.sfx(sfx.whoosh(0.5, 'swoosh', direction=1, peak=0.4, seed=6), at=C['charsOut'] - 0.02, gain=-12)
btn = m.track('button', level=-24, sends={'hall': -12})
btn.add(mar.play('G5', dur=0.5, vel=0.6), 8.7); btn.add(mar.play('C6', dur=1.0, vel=0.65), 8.85)

if __name__ == '__main__':
    out = os.path.join(HERE, 'out'); os.makedirs(out, exist_ok=True)
    res = m.export(os.path.join(out, 'audio.wav'), spectrogram=os.path.join(out, 'audio_spec.png'))
    m.report()
    print({k: res[k] for k in ('duration', 'lufs', 'true_peak', 'sample_peak', 'stereo_corr', 'warnings') if k in res})
