"""BRMG event floor plan — soundtrack (15 s, 120 bpm, A minor).

A rhythmic build: every placement on the plan lands on a snare (stage -> tables on quarters -> truss on eighths ->
booths on sixteenths -> the two headline lines). Kick on every beat, hats thickening with the grid, a riser into
EVENT. Then the plan 'plays': each object sounds a note the moment the light sweeps over it (times derived from the
same geometry as the picture), the red flood drops on 10.5, and brmgdc.com types out on sixteenths.
Everything reads cues.json (single source of truth for picture and sound).
"""
import sys, os, json, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'audio'))
import mgaudio as mg
from mgaudio import sfx, drums, fm, samples, synth

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'cues.json')))
FPS, BPM, DUR = C['fps'], C['bpm'], float(C['duration'])
M = C['M']; OX, OY = C['plan']['origin']; PX, PY = C['pivot']
BEAT = 60.0 / BPM
frame = lambda t: round(t * FPS) / FPS          # picture changes on frame boundaries

m = mg.Mix(duration=DUR, bpm=BPM, anchor=0.0)
m.group('music').level = -20
m.sfx_duck = 2.0

MAR = samples.inst('marimba')


def bell(note, dur=0.3, vel=0.8):
    return fm.bell(note, dur, vel, 'glock')       # glock samples are LFS pointers in this clone: synthesise


def mallet(note, vel=0.8, dur=0.4):
    b = fm.mallet(note, dur * 0.8, vel * 0.8, 'marimba')
    try:
        a = MAR.play(note, dur=dur, vel=vel, release=0.12)
        return mg.layer([(a, 0, 0, 0), (b, 0, -8, 0)])
    except Exception:
        return b


tk = m.track('kick', level=-18)
tsn = m.track('snare', level=-21, sends={'room': -14})
tcl = m.track('clap', level=-27, sends={'room': -10})
thh = m.track('hat', level=-33, pan=-0.2)
toh = m.track('ohat', level=-35, pan=0.2)
tbs = m.track('bass', level=-24)
tmr = m.track('mallet', level=-22, sends={'room': -12, 'plate': -16}, pan=0.1)
tgl = m.track('glock', level=-27, sends={'room': -10, 'plate': -14})
tpd = m.track('pad', level=-30, sends={'plate': -8})

pan_x = lambda x: max(-0.7, min(0.7, (x - 540) / 540 * 0.7))
P = C['placements']
LAST_BUILD = max(p['t'] for p in P)         # 6.125
HL = C['headline']
FLOOD0, FLOOD1 = C['flood']['t0'], C['flood']['t1']


def cell_centre(p):
    return OX + p['cell'][0] * M + M / 2, OY + p['cell'][1] * M + M / 2


# ------------------------------------------------------------------ grid draws (plotter ticks on sixteenths)
for k in range(8):
    m.sfx(sfx.tick('wood' if k % 2 == 0 else 'hi'), at=k * 0.0625, gain=-9 + 0.3 * k, pan=(-1) ** k * 0.4)
m.sfx(sfx.zip_(True, dur=0.35), at=0.1, gain=-12)

# ------------------------------------------------------------------ the build: one snare per placement
n = len(P) + len(HL)
for i, p in enumerate(P):
    t = p['t']
    x, _ = cell_centre(p)
    vel = 0.55 + 0.45 * i / (n - 1)
    tune = {'stage': -2, 'table': 0, 'truss': 1, 'booth': 3}[p['kind']] + 0.12 * i
    tsn.add(drums.snare('tight', vel, tune=tune), t, pan=pan_x(x) * 0.5)
    if p['kind'] == 'stage':
        m.sfx(sfx.impact('thud', size=0.7), at=t, gain=-5)
    elif p['kind'] == 'table':
        m.sfx(sfx.blip(['A3', 'C4', 'E4', 'A3', 'C4', 'E4'][int(p['id'][-1]) - 1], 'sine', dur=0.12, glide=0.6), at=t, gain=-9, pan=pan_x(x))
    elif p['kind'] == 'truss':
        m.sfx(sfx.click('hard'), at=t, gain=-8, pan=pan_x(x))
        tgl.add(bell(['E5', 'G5', 'A5', 'C6', 'E6'][int(p['id'][-1]) - 1], 0.2, 0.7), t, pan=pan_x(x))
    elif p['kind'] == 'booth':
        m.sfx(sfx.tick('clock'), at=t, gain=-8, pan=pan_x(x))
        m.sfx(sfx.pop('soft', 1.3 + 0.08 * int(p['id'][-1])), at=t, gain=-12, pan=pan_x(x))

# headline lines: snare + clap + weight
for j, h in enumerate(HL):
    t = h['t']
    tsn.add(drums.snare('fat', 1.0, tune=-1 + 2 * j), t)
    tcl.add(drums.clap('tight', 0.95), t)
    m.sfx(sfx.impact('punch', size=0.9 - 0.15 * j), at=t, gain=-3 - j)
    m.sfx(sfx.swish(0.4, direction=-1 if j == 0 else 1, seed=11 + j), at=t - 0.4, gain=-9)

# kick on every beat from the stage landing to the flood-in; hats thicken as the grid fills
for k in range(1, int(round(FLOOD0 / BEAT))):
    t = k * BEAT
    if t < 1.0 - 1e-6 or t >= FLOOD0 - 1e-6:
        continue
    tk.add(drums.kick('techno', 0.8 if t < 4 else 0.9, decay=0.34), t)
tk.add(drums.kick('techno', 0.7, decay=0.3), 0.5)                      # stage landing
for k in range(int((LAST_BUILD + 0.4) / 0.25)):                         # eighth hats 1.0 -> 7.0
    t = 1.0 + k * 0.25
    if t >= 7.5: break
    off = (k % 2 == 1)
    thh.add(drums.hat('closed', 0.55 + (0.2 if off else 0.0) + 0.02 * k, decay=0.03), t)
for k in range(8):                                                       # sixteenth hat roll under the booths
    thh.add(drums.hat('closed', 0.45 + 0.05 * k, decay=0.02), 5.5 + 0.0625 + k * 0.125)
for t in [x * 0.5 + 0.25 for x in range(2, 14)]:                         # open hats on the off-beat
    toh.add(drums.hat('open', 0.55, decay=0.14), t)

# riser into EVENT
m.sfx(sfx.riser(2.0, 'hybrid', note='A3', intensity=0.9, end='cut', seed=5), at=4.5, gain=-10)
# bass: rolling off-beat A minor from the trusses to the flood
bass_notes = ['A1', 'A1', 'C2', 'A1', 'E2', 'A1', 'D2', 'E2']
for k in range(int((FLOOD0 - 3.0) / 0.5)):
    t = 3.25 + k * 0.5
    if t >= FLOOD0: break
    m.sfx(sfx.blip(bass_notes[k % len(bass_notes)].replace('1', '2'), 'sine', dur=0.22, glide=1.0), at=t, gain=-9)

# ------------------------------------------------------------------ the plan plays: notes when the light crosses
def ang(cx, cy):
    return math.degrees(math.atan2(cy - PY, cx - PX))


def crossing(sw, a):
    lo, hi = sorted((sw['a0'], sw['a1']))
    if not (lo - 1e-6 <= a <= hi + 1e-6): return None
    return sw['t0'] + (a - sw['a0']) / (sw['a1'] - sw['a0']) * (sw['t1'] - sw['t0'])


TABLE_N = {'table1': 'A4', 'table2': 'E4', 'table3': 'C5', 'table4': 'E4', 'table5': 'A3', 'table6': 'D4'}
TRUSS_N = ['A5', 'C6', 'E6', 'G6', 'A6']
BOOTH_N = {'booth1': 'C5', 'booth2': 'G5', 'booth3': 'D5', 'booth4': 'A5', 'booth5': 'E5', 'booth6': 'C6'}
shift = {'A': 0, 'B': -12, 'C': 12}
SC = {'A': 0, 'B': 1, 'C': 2}
from mgaudio import theory
def transpose(n, semi):
    if semi == 0: return n
    name, octv = n[:-1], int(n[-1])
    return f"{name}{octv + semi // 12}"
heard = []
for sw in C['sweeps']:
    sid = sw['id']
    m.sfx(sfx.whoosh(sw['t1'] - sw['t0'], 'swoosh', direction=1 if sw['a1'] < sw['a0'] else -1, peak=0.55, seed=20 + SC[sid]),
          at=sw['t0'] - 0.05, gain=-9 if sid != 'C' else -7)
    for p in P:
        if p['kind'] == 'stage': continue
        cx, cy = cell_centre(p)
        t = crossing(sw, ang(cx, cy))
        if t is None: continue
        t = frame(t)
        if p['kind'] == 'table': note, snd = TABLE_N[p['id']], 'mar'
        elif p['kind'] == 'truss': note, snd = TRUSS_N[int(p['id'][-1]) - 1], 'glk'
        else: note, snd = BOOTH_N[p['id']], 'mar'
        note = transpose(note, shift[sid])
        if snd == 'mar': tmr.add(mallet(note, 0.85, 0.5 if sid != 'B' else 0.8), t, pan=pan_x(cx))
        else: tgl.add(bell(note, 0.3, 0.8), t, pan=pan_x(cx))
        heard.append((sid, p['id'], round(t, 3)))
    # beam on/off marks on the beat
    m.sfx(sfx.click('soft'), at=sw['t0'], gain=-8)
    tsn.add(drums.snare('tight', 0.7, tune=2 if sid == 'C' else 0), sw['t0'] + (0.0 if sid != 'A' else 0.0), pan=0.0)

# during the sweeps the pulse keeps going: kick on beats (above), clap on 2 and 4
for k in range(int(round(7.5 / BEAT)), int(round(FLOOD0 / BEAT))):
    t = k * BEAT
    if k % 2 == 1: tcl.add(drums.clap('tight', 0.7), t)

# ------------------------------------------------------------------ red flood = the drop
m.mute(FLOOD0 - 0.125, 0.12)                                              # 1/8 beat of air before the hit
m.sfx(sfx.impact('punch', size=1.25), at=FLOOD0, gain=1)
m.sfx(sfx.sub_drop(1.2), at=FLOOD0, gain=-9)
m.sfx(drums.crash(), at=FLOOD0, gain=-10)
m.sfx(synth.stab(['A3', 'C4', 'E4', 'G4', 'B4'], 0.5, 0.9, 'dub'), at=FLOOD0, gain=-5)
m.sfx(sfx.whoosh(FLOOD1 - FLOOD0, 'swoosh', direction=1, peak=0.65, seed=33), at=FLOOD0, gain=-8)
tk.add(drums.kick('techno', 1.0, decay=0.4), FLOOD0)
for k in range(int(round(FLOOD0 / BEAT)), int(round(13.5 / BEAT))):
    t = k * BEAT
    if t > FLOOD0 + 1e-6: tk.add(drums.kick('techno', 0.95, decay=0.36), t)
    if k % 2 == 1: tcl.add(drums.clap('tight', 0.8), t)
    for h in (0.25,):
        thh.add(drums.hat('closed', 0.6, decay=0.03), t + h)
    toh.add(drums.hat('open', 0.55, decay=0.14), t + 0.25)
for k in range(int(round(FLOOD0 / BEAT)), int(round(13.5 / BEAT))):
    t = 0.25 + k * BEAT
    if t < 13.5:
        m.sfx(sfx.blip(['A2', 'A2', 'C3', 'E2'][k % 4], 'sine', dur=0.22, glide=1.0), at=t, gain=-8)
m.sfx(synth.stab(['A3', 'C4', 'E4', 'G4', 'B4'], 0.45, 0.8, 'dub'), at=FLOOD1, gain=-8)

# rule + url typing, one tick per sixteenth, climbing the pentatonic
m.sfx(sfx.zip_(True, dur=0.4), at=C['rule']['t0'] + 0.05, gain=-11)
U = C['url']; scale = ['A5', 'C6', 'D6', 'E6', 'G6', 'A6', 'C7', 'E6', 'G6', 'A6']
for i, ch in enumerate(U['text']):
    t = U['t0'] + i * U['step']
    m.sfx(sfx.tick('clock'), at=t, gain=-8, pan=-0.3 + 0.06 * i)
    tgl.add(bell(scale[i], 0.12, 0.55 + 0.04 * i), t, pan=-0.3 + 0.06 * i)
tend = U['t0'] + (len(U['text']) - 1) * U['step']
m.sfx(sfx.ding('E6'), at=tend + 0.02, gain=-9, pan=0.2)
m.sfx(synth.stab(['A2', 'E3', 'A3', 'C4', 'E4'], 0.6, 0.7, 'dub'), at=tend + 0.125, gain=-7)
tpd.add(synth.pad(['A3', 'C4', 'E4', 'B4'], DUR - FLOOD1, 0.6, 'warm'), FLOOD1)

os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
res = m.export(os.path.join(HERE, 'out', 'audio.wav'), lufs=-14, tp=-1.3, spectrogram=os.path.join(HERE, 'out', 'audio_spec.png'))
m.report()
print(len(heard), 'light-plays notes')
print({k: res[k] for k in ('duration', 'lufs', 'true_peak', 'warnings') if k in res})
