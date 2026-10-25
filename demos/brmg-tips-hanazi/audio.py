"""BRMG 3-tips film — soundtrack (15 s, 120 bpm, C major pop-percussion groove).

Kick / clap / snap / shaker / congas / cowbell, a bouncy sub bass and marimba stabs on the off-beats, locked to
cues.json. Every scene change gets a whoosh (peak on the landing), every numeral lands on a boing + kick, every caption
character pops on its own tick (2-frame stagger, same as the picture), the hero tip 3 gets a riser + crash, and the
badge + brmgdc.com land on a chime run.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'audio'))
import mgaudio as mg
from mgaudio import sfx, drums, fm, samples, synth

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'cues.json')))
FPS, BPM, DUR = C['fps'], C['bpm'], float(C['duration'])
BEAT = 60 / BPM
STEP = BEAT / 4                       # sixteenth
TRANS, STAG = C['trans'], C['stagger']
SC = {s['id']: s for s in C['scenes']}
S = [s['S'] for s in C['scenes']]     # 0, 2.0, 5.5, 9.0, 12.5
frame = lambda t: round(t * FPS) / FPS

m = mg.Mix(duration=DUR, bpm=BPM, anchor=0.0)
m.group('music').level = -19
m.sfx_duck = 2.0

MAR = samples.inst('marimba')


def mallet(note, vel=0.8, dur=0.3):
    b = fm.mallet(note, dur * 0.8, vel * 0.8, 'marimba')
    try:
        a = MAR.play(note, dur=dur, vel=vel, release=0.1)
        return mg.layer([(a, 0, 0, 0), (b, 0, -8, 0)])
    except Exception:
        return b


tk = m.track('kick', level=-18)
tcl = m.track('clap', level=-22, sends={'room': -10})
tsn = m.track('snap', level=-27, pan=0.3)
tsh = m.track('shaker', level=-30, pan=0.25)
tcg = m.track('conga', level=-24, sends={'room': -12}, pan=-0.35)
tcb = m.track('cowbell', level=-31, pan=0.4)
tbs = m.track('bass', level=-23)
tmr = m.track('marimba', level=-24, sends={'room': -12, 'plate': -16}, pan=0.1)
tbl = m.track('bell', level=-29, sends={'plate': -10})

END_GROOVE = 14.0
# ------------------------------------------------------------------ the groove (16th grid, 2 s bars)
def bars(t0, t1):
    k = int(t0 / (BEAT * 4) + 1e-6)
    while k * BEAT * 4 < t1 - 1e-6:
        yield k, k * BEAT * 4
        k += 1


KICK = 'x.......x.x.....'
CLAP = '....x.......x...'
SHK = 'xxxxxxxxxxxxxxxx'
CONGA = '..x...x..x..x...'
COWB = '.x.x...x.x...x..'
for k, b0 in bars(0.0, END_GROOVE):
    if b0 + 2 * BEAT > END_GROOVE + 1e-6 and b0 >= END_GROOVE: break
    full = b0 >= S[1] - 1e-6            # the full groove starts with tip 1
    for i, ch in enumerate(KICK):
        t = b0 + i * STEP
        if ch == 'x' and t < END_GROOVE: tk.add(drums.kick('punchy', 0.9 if i == 0 else 0.75, decay=0.28), t)
    if b0 < S[1] - 1e-6 and k == 0:     # intro: kick only on 1 and 3 + a build
        pass
    for i, ch in enumerate(SHK):
        t = b0 + i * STEP
        if t < END_GROOVE: tsh.add(drums.shaker(0.35 + (0.18 if i % 4 == 2 else 0) + (0.08 if i % 2 else 0), accent=(i % 4 == 2)), t)
    if full or b0 >= 1.0:
        for i, ch in enumerate(CLAP):
            t = b0 + i * STEP
            if ch == 'x' and t < END_GROOVE:
                tcl.add(drums.clap('tight', 0.85), t); tsn.add(drums.snap(0.8), t)
        for i, ch in enumerate(CONGA):
            t = b0 + i * STEP
            if ch == 'x' and t < END_GROOVE: tcg.add(drums.tom('high' if i % 3 else 'mid', 0.7, tune=3), t)
        for i, ch in enumerate(COWB):
            t = b0 + i * STEP
            if ch == 'x' and t < END_GROOVE and b0 >= S[2] - 1e-6: tcb.add(drums.cowbell(0.5), t)

# chords per bar (I V vi IV) : bass root + marimba stabs on the off-beat 16ths
PROG = [('C', ['C4', 'E4', 'G4'], 'C2'), ('G', ['B3', 'D4', 'G4'], 'G1'), ('A', ['C4', 'E4', 'A4'], 'A1'), ('F', ['C4', 'F4', 'A4'], 'F1')]
STAB = [2, 5, 6, 10, 13]               # sixteenth steps
for k, b0 in bars(0.0, END_GROOVE):
    name, chord, root = PROG[k % 4]
    for i in (0, 3, 6, 8, 11, 14):      # bouncy bass: root, then octave jumps
        t = b0 + i * STEP
        if t >= END_GROOVE or (k == 0 and t < 0.01 and False): continue
        note = root if i not in (6, 14) else root[0] + str(int(root[1]) + 1)
        m.sfx(sfx.blip(note, 'sine', dur=0.2, glide=1.0), at=t, gain=-8)
    if b0 >= S[1] - 1e-6:
        for j, i in enumerate(STAB):
            t = b0 + i * STEP
            if t >= END_GROOVE: continue
            for n in chord: tmr.add(mallet(n, 0.55 + 0.1 * (j % 2), 0.22), t, pan=-0.15 + 0.1 * j)

# ------------------------------------------------------------------ intro: title pops + build into tip 1
m.sfx(sfx.boing(1.1, 0.6), at=0.0, gain=-8)
m.sfx(sfx.impact('thud', size=0.9), at=0.0, gain=-5)
for k in range(6):                                                    # '3 TIPS' character pops (2-frame stagger)
    m.sfx(sfx.pop('soft', 1.0 + 0.08 * k), at=frame(0.0 + k * STAG), gain=-11, pan=-0.3 + 0.12 * k)
m.sfx(sfx.pop('bubble', 1.2), at=C['intro']['micro_t'], gain=-11)
for tt in C['intro']['sparkle_t']: m.sfx(sfx.shimmer_hit('E6'), at=tt, gain=-14, pan=0.3)
for k in range(8):                                                    # snare-ish build into tip 1 (sixteenth roll)
    t = S[1] - 0.5 + k * STEP * 1.0
    tcl.add(drums.clap('tight', 0.45 + 0.07 * k), t)
m.sfx(sfx.slide_whistle(True, 0.45, lo=600, hi=2300), at=S[1] - TRANS - 0.35, gain=-12)

# ------------------------------------------------------------------ scene changes: whoosh peaking on the landing
for i in range(1, 5):
    land = S[i]
    m.sfx(sfx.whoosh(0.55, 'swoosh', direction=1 if i % 2 else -1, peak=0.6, seed=40 + i), at=land - 0.55 * 0.6, gain=-4 if i != 4 else -3)

# ------------------------------------------------------------------ the tips
for i, sid in enumerate(['t1', 't2', 't3']):
    sc = SC[sid]
    t0 = sc['numeral_t']
    m.sfx(sfx.boing([1.0, 1.15, 0.9][i], 0.7), at=t0, gain=-7)
    m.sfx(sfx.impact('thud', size=0.9), at=t0, gain=-4)
    m.sfx(sfx.pop('bubble', 0.9 + 0.15 * i), at=t0, gain=-9)
    # hop on every beat while the numeral holds: soft wood tick on the landing
    for b in range(1, 6):
        m.sfx(sfx.tick('wood'), at=t0 + b * BEAT, gain=-17, pan=0.0)
    for k, ln in enumerate(sc['lines']):
        lt = sc['line_t'][k]
        m.sfx(sfx.whoosh(0.32, 'swish', direction=-1 if k % 2 else 1, peak=0.5, seed=60 + 3 * i + k), at=lt - 0.16, gain=-13)
        for c, ch in enumerate(ln):
            if ch == ' ': continue
            m.sfx(sfx.pop('soft', 0.95 + 0.06 * c + 0.08 * k), at=frame(lt + c * STAG), gain=-12, pan=-0.35 + 0.1 * c)
        tmr.add(mallet(['C5', 'E5', 'G5'][k] if i != 1 else ['A4', 'C5', 'E5'][k], 0.8, 0.3), lt, pan=0.0)
    m.sfx(sfx.ding(['E6', 'G6', 'C7'][i]), at=sc['icon_t'], gain=-10, pan=0.4)
    m.sfx(sfx.pop('mouth', 1.3), at=sc['icon_t'], gain=-11, pan=0.4)
    for k, st in enumerate(sc['sparkle_t']):
        m.sfx(sfx.shimmer_hit(['G6', 'E6', 'C7'][k]), at=st + 0.03, gain=-14, pan=-0.4 + 0.4 * k)

# hero (tip 3, 60 %): riser into the hit, then punch + crash + stab
m.sfx(sfx.riser(1.0, 'hybrid', note='G3', intensity=1.0, end='cut', seed=7), at=S[3] - 1.2, gain=-9)
m.sfx(sfx.impact('punch', size=1.2), at=S[3], gain=-1)
m.sfx(drums.crash(), at=S[3], gain=-11)
m.sfx(synth.stab(['C4', 'E4', 'G4', 'B4'], 0.45, 0.85, 'dub'), at=S[3], gain=-8)

# ------------------------------------------------------------------ final: badge + brmgdc.com
F = C['final']
m.sfx(sfx.impact('punch', size=1.0), at=F['badge_t'], gain=-2)
m.sfx(sfx.boing(1.25, 0.7), at=F['badge_t'], gain=-8)
m.sfx(drums.crash(), at=F['badge_t'], gain=-12)
m.sfx(sfx.chime(('C6', 'E6', 'G6', 'C7'), 0.07, 'celesta'), at=F['badge_t'] + 0.05, gain=-9)
for c, ch in enumerate(F['url']):
    t = frame(F['url_t'] + c * STAG)
    m.sfx(sfx.pop('soft', 1.0 + 0.07 * c), at=t, gain=-11, pan=-0.4 + 0.09 * c)
    tbl.add(fm.bell(['C6', 'D6', 'E6', 'G6', 'A6', 'C7', 'A6', 'G6', 'E6', 'C7'][c], 0.25, 0.6, 'glock'), t, pan=-0.4 + 0.09 * c)
for k, st in enumerate(F['sparkle_t']):
    m.sfx(sfx.shimmer_hit(['G6', 'E6', 'C7'][k]), at=st + 0.03, gain=-13, pan=-0.4 + 0.4 * k)
tend = F['url_t'] + len(F['url']) * STAG
m.sfx(sfx.ding('G6'), at=tend + 0.1, gain=-9, pan=0.2)
m.sfx(synth.stab(['C3', 'G3', 'C4', 'E4', 'G4'], 0.9, 0.8, 'dub'), at=tend + 0.05, gain=-9)
m.sfx(synth.pad(['C4', 'E4', 'G4', 'B4'], DUR - 12.5, 0.6, 'warm'), at=12.5, gain=-16)

os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
res = m.export(os.path.join(HERE, 'out', 'audio.wav'), lufs=-14, tp=-1.3, spectrogram=os.path.join(HERE, 'out', 'audio_spec.png'))
m.report()
print({k: res[k] for k in ('duration', 'lufs', 'true_peak', 'warnings') if k in res})
