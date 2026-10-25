"""BRMG notebook checklist — soundtrack (15 s, 96 bpm, bar anchor 0.5 s).

Pencil taps and scratches, page flips, a light percussive pulse (shaker, soft kick, rim) and a marimba note on every
icon landing. Everything reads cues.json, so picture and sound share one cue sheet. Picture hits land on even frames
(animated on 2s), so every hit time is snapped to the drawing it belongs to.
Form: page opens -> four rows build (tap, scratch, tick, icon thud + marimba) -> page flip + paper slide as the camera
drops -> line built letter by letter -> red underline resolves on a marimba chord -> email, pulse thins out.
"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'audio'))
import mgaudio as mg
from mgaudio import sfx, drums, fm, samples

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'cues.json')))
FPS = C['fps']
BPM, A0 = C['bpm'], C['bar_anchor']
BEAT = 60 / BPM
DUR = float(C['duration'])


def vis(t):
    """First drawing (even frame) at or after t: when the picture actually shows the event."""
    return math.ceil(t * FPS / 2 - 1e-6) * 2 / FPS


m = mg.Mix(duration=DUR, bpm=BPM, anchor=A0)
m.group('music').level = -21
m.sfx_duck = 2.0

MAR = samples.inst('marimba')
GLK = samples.inst('glock')


def mallet(note, vel=0.8, dur=0.4):
    a = MAR.play(note, dur=dur, vel=vel, release=0.12)
    b = fm.mallet(note, dur * 0.8, vel * 0.8, 'marimba')
    return mg.layer([(a, 0, 0, 0), (b, 0, -8, 0)])


# ------------------------------------------------------------ light percussive pulse
tsh = m.track('shaker', level=-30, sends={'room': -12}, pan=0.2)
tkk = m.track('kick', level=-27)
trm = m.track('rim', level=-31, sends={'room': -10}, pan=-0.15)
tmr = m.track('marimba', level=-24, sends={'room': -12, 'plate': -18}, pan=0.1)

ROWS = C['rows']
END_PULSE = 13.0
tsh.loop(lambda v: drums.shaker(v), 'x.x.x.x.x.x.x.x.', A0, 14.6, vel=0.5, humanize=0.004, vel_jitter=0.12)
tkk.loop(lambda v: drums.kick('soft', v), 'x.......x.......', ROWS[1], END_PULSE, vel=0.6)
trm.loop(lambda v: drums.rim(v), '....x.......x...', ROWS[1], END_PULSE, vel=0.5, humanize=0.003)
# tiny pickup into the first bar
tkk.add(drums.kick('soft', 0.5), A0)

# ------------------------------------------------------------ rows
NOTES = ['C5', 'E5', 'G5', 'C6']
REL = C['rel']
for i, s in enumerate(ROWS):
    # box: four quick pencil taps along its sides + a wooden tap on the first corner
    t_box = vis(s + REL['box'])
    m.sfx(sfx.pen('pencil', 0.32, strokes=[(0.0, 0.07), (0.08, 0.07), (0.16, 0.07), (0.24, 0.07)], seed=10 + i), at=t_box, gain=-7, pan=-0.3)
    m.sfx(sfx.tick('wood'), at=t_box, gain=-6, pan=-0.3)
    # word: one pencil scratch under the letters, soft pop on the first letter
    t_w = vis(s + REL['word'])
    m.sfx(sfx.pen('pencil', 0.38, seed=20 + i), at=t_w, gain=-9, pan=0.0)
    m.sfx(sfx.pop('soft', 1.0 + 0.05 * i), at=t_w, gain=-10)
    # red tick: two scribbled passes
    t_t = vis(s + REL['tick'])
    m.sfx(sfx.pen('pencil', 0.34, strokes=[(0.0, 0.16), (0.17, 0.16)], seed=30 + i), at=t_t, gain=-5, pan=0.25)
    # icon: lands at +0.13 s, re-bounces at +0.34 s
    t_i = s + REL['icon']
    land1, land2 = vis(t_i + 0.13), vis(t_i + 0.34)
    m.sfx(sfx.impact('soft', 0.55), at=land1, gain=-11, pan=0.3)
    m.sfx(sfx.pop('bubble', 1.0 + 0.1 * i), at=land1, gain=-9, pan=0.3)
    m.sfx(sfx.tick('wood'), at=land2, gain=-12, pan=0.3)
    tmr.add(mallet(NOTES[i], 0.85), land1)
    tmr.add(mallet(NOTES[i], 0.5), land2 + 0.0, gain=-6)

# ------------------------------------------------------------ opening + header
m.sfx(sfx.paper('flip', 0.4, seed=1), at=C['sfx']['page_open'], gain=-6, pan=0.1)
m.sfx(sfx.pen('marker', 0.5, seed=2), at=0.0, gain=-12, pan=-0.2)   # 'the list.' lettering
m.sfx(sfx.pop('soft', 0.9), at=0.04, gain=-9)

# ------------------------------------------------------------ camera drops down the page
s0, s1 = C['slide']
m.sfx(sfx.paper('flip', 0.35, seed=5), at=C['sfx']['page_flip_slide'], gain=-5, pan=0.15)
m.sfx(sfx.paper('slide', 1.8, seed=6), at=C['sfx']['slide_whoosh'], gain=-8, pan=0.0)
m.sfx(sfx.whoosh(1.5, 'soft', direction=1, peak=0.55, seed=3), at=C['sfx']['slide_whoosh'], gain=-11)
# rising marimba sweep underneath the slide
for k, n in enumerate(['C5', 'E5', 'G5', 'A5', 'C6']):
    tmr.add(mallet(n, 0.45 + 0.07 * k, 0.3), s0 + 0.35 * k, gain=-8)

# ------------------------------------------------------------ closing line, letter by letter
for i, l in enumerate(C['lines']):
    t_l = vis(l['start'])
    m.sfx(sfx.pen('pencil', 0.34 + 0.02 * len(l['text']), seed=40 + i), at=t_l, gain=-8, pan=-0.2 + 0.13 * i)
    m.sfx(sfx.pop('soft', 1.0 + 0.04 * i), at=t_l, gain=-11)

# red underline resolves on a chord
u0, u1 = C['underline']
m.sfx(sfx.pen('marker', 0.36, strokes=[(0.0, 0.2), (0.17, 0.19)], seed=50), at=vis(u0), gain=-6, pan=0.2)
R = vis(u1)
for n, g in (('C4', -4), ('G4', -5), ('E5', -4), ('D5', -7), ('C6', -6)):
    tmr.add(mallet(n, 0.9, 0.9), R, gain=g)
m.sfx(sfx.ding('E6'), at=R, gain=-12, pan=0.2)
m.sfx(sfx.sub_drop(0.4, 70.0, 45.0), at=R, gain=-7)
tkk.add(drums.kick('soft', 0.9), R)
trm.add(drums.rim(0.8), R)

# ------------------------------------------------------------ contact
e0 = vis(C['email']['start'])
m.sfx(sfx.pen('pen', 0.5, seed=60), at=e0, gain=-15, pan=0.0)
m.sfx(sfx.sparkle(0.9, 8, key='C', mode='major_pentatonic', seed=61), at=e0 + 0.1, gain=-16, pan=0.2)

os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
res = m.export(os.path.join(HERE, 'out/audio.wav'), spectrogram=os.path.join(HERE, 'out/audio_spec.png'))
m.report()
print({k: res[k] for k in ('duration', 'lufs', 'true_peak', 'warnings') if k in res})
