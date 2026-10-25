"""BRMG "Backstage Pass" — soundtrack (15 s, 120 bpm).

Crowd murmur (distant in the corridor, muffled in the dressing room, open at the side-stage, a roar on SHOW TIME!!),
a go-go-style conga groove (congas + cowbell + shaker + kick, clap on 2 and 4) that drops in on the first hard cut,
a pop on every caption character (same 2-frame stagger as the picture), shutter + whoosh on each cut, thumps on the zoom
punches, a build into the hero hit at 9.0, hearts + upload chime on the phone clip and a chime run on the end card.
Everything is read from cues.json, the same cue sheet the picture uses.
"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib', 'audio'))
import mgaudio as mg
from mgaudio import sfx, drums, fm, samples, synth
from mgaudio import filters as F
from mgaudio.core import SR, Sound, ns, rng, pink, white

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'cues.json')))
FPS, BPM, DUR = C['fps'], C['bpm'], float(C['duration'])
BEAT = 60 / BPM
STEP = BEAT / 4
STAG = C['stagger']
SC = {s['id']: s for s in C['scenes']}
FIN = C['final']
HERO = C['hero_t']
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
tcl = m.track('clap', level=-23, sends={'room': -10})
tsh = m.track('shaker', level=-31, pan=0.25)
tcg = m.track('conga', level=-22, sends={'room': -12}, pan=-0.3)
tcb = m.track('cowbell', level=-31, pan=0.4)
tbs = m.track('bass', level=-23)
tmr = m.track('marimba', level=-24, sends={'room': -12, 'plate': -16}, pan=0.1)
tbl = m.track('bell', level=-29, sends={'plate': -10})
tcr = m.track('crowd', level=-30, sends={'room': -14})


# ------------------------------------------------------------------ crowd bed
def murmur(dur, seed, vowels=('a', 'o', 'e'), lo=180.0, hi=3400.0, lp=None):
    """Voices-in-a-room: band-passed pink noise through vowel formants, each layer with its own syllable-rate AM."""
    n = ns(dur)
    r = rng(seed)
    out = np.zeros(n)
    t = np.arange(n) / SR
    for k, v in enumerate(vowels):
        x = F.bpf(pink(n, seed=seed * 7 + k), lo, hi)
        x = F.formant(x, v, q=6.0, mix=0.8)
        # syllable AM: ~3-6 Hz, random phase/rate drift
        f = 3.0 + 3.0 * r.random()
        ph = r.random() * 6.28
        drift = np.cumsum(F.lpf(r.standard_normal(n), 1.5)) / SR * 2.5
        env = 0.55 + 0.45 * np.sin(2 * np.pi * f * t + ph + drift * 6.0)
        env = env ** 1.8
        out += x * env
    out /= (np.std(out) + 1e-9)
    if lp:
        out = F.lpf(out, lp)
    return out * 0.25


def crackle(dur, seed, density=900.0):
    """Applause-like crackle: random impulses through a band-pass."""
    n = ns(dur)
    r = rng(seed)
    imp = (r.random(n) < density / SR).astype(float) * r.standard_normal(n)
    y = F.bpf(imp, 900, 6500)
    return y / (np.std(y) + 1e-9) * 0.25


def env_curve(points, n):
    ts = np.arange(n) / SR
    pts = np.array(points, dtype=float)
    db = np.interp(ts, pts[:, 0], pts[:, 1])
    return 10 ** (db / 20)


def stereo(x, seed):
    r = rng(seed)
    d = int(0.011 * SR)
    return np.stack([x, np.roll(x, d) * 0.9 + 0.0 * r.random()])


N = ns(DUR)
# distant + muffled bed (corridor, dressing room): lowpassed, loud first, ducks away at the side-stage cut
bed_a = murmur(DUR, 11, lp=1700.0)
bed_a *= env_curve([(0, -9), (3.4, -9), (3.5, -8), (6.9, -9), (7.0, -60), (15, -60)], N)
# open bed (side-stage, phone clip): full band, opens at 7.0, swells into the hero, then falls away
bed_b = murmur(DUR, 23, vowels=('a', 'e', 'o'), lo=200.0, hi=5200.0)
bed_b *= env_curve([(0, -60), (6.99, -60), (7.0, -9), (8.4, -7), (9.0, -3), (10.2, -7), (10.5, -12), (12.0, -14), (12.5, -60), (15, -60)], N)
# applause crackle + roar on SHOW TIME!!
rear = crackle(DUR, 31, 1400.0) * env_curve([(0, -80), (8.99, -80), (9.0, -3), (9.6, -5), (10.5, -14), (11.0, -80), (15, -80)], N)
roar = F.bpf(pink(N, seed=41), 250, 2600) * env_curve([(0, -80), (8.2, -80), (9.0, -2), (9.9, -6), (10.8, -22), (11.2, -80), (15, -80)], N)
crowd = stereo(bed_a, 1) + stereo(bed_b, 2) + stereo(rear, 3) * 0.5 + stereo(roar, 4) * 0.7
tcr.add(Sound(crowd), 0.0)

# ------------------------------------------------------------------ groove: go-go conga pattern on a 16th grid (2 s bars)
KICK = 'x.......x..x....'
CLAP = '....x.......x...'
SHK = 'xxxxxxxxxxxxxxxx'
CONGA_L = 'x..x..x.....x...'
CONGA_M = '..x...x...x...x.'
CONGA_H = '...x..x..x..x..x'
COWB = 'x.x.x.x.x.x.x.x.'
BASS = ['A1', 'F1', 'C2', 'G1']
STAB = [2, 5, 6, 10, 13]
PROG = [['A3', 'C4', 'E4'], ['F3', 'A3', 'C4'], ['C4', 'E4', 'G4'], ['G3', 'B3', 'D4']]


def on(t, lo, hi):
    return lo - 1e-6 <= t < hi - 1e-6


GROOVE_END = FIN['S'] + 1.5
bar = 0
while bar * 4 * BEAT < DUR:
    b0 = bar * 4 * BEAT
    for i in range(16):
        t = b0 + i * STEP
        if t >= GROOVE_END:
            break
        full = on(t, 3.5, 8.5) or on(t, 9.0, GROOVE_END)       # drops in on the first hard cut, breaks for the build 8.5-9.0
        light = on(t, 0.0, 3.5)                                   # corridor: sparse, distant
        if full or light:
            v = 1.0 if full else 0.45
            if KICK[i] == 'x' and (full or i in (0, 8)):
                tk.add(drums.kick('punchy', (0.9 if i == 0 else 0.75) * v, decay=0.26), t)
            if SHK[i] == 'x':
                tsh.add(drums.shaker(((0.35 + (0.18 if i % 4 == 2 else 0) + (0.08 if i % 2 else 0))) * v, accent=(i % 4 == 2)), t)
            if CONGA_L[i] == 'x':
                tcg.add(drums.tom('low', 0.78 * v, tune=-2), t, pan=-0.35)
            if CONGA_M[i] == 'x':
                tcg.add(drums.tom('mid', 0.72 * v, tune=1), t, pan=-0.25)
            if CONGA_H[i] == 'x' and full:
                tcg.add(drums.tom('high', 0.68, tune=3), t, pan=-0.15)
        if full and CLAP[i] == 'x':
            tcl.add(drums.clap('tight', 0.85), t)
        if full and on(t, 7.0, 8.5) or (on(t, 9.0, GROOVE_END) and full):
            if COWB[i] == 'x':
                tcb.add(drums.cowbell(0.5 if i % 4 else 0.6), t)
        # bass blips + marimba stabs
        if full or (light and i in (0, 8)):
            if i in (0, 3, 6, 8, 11, 14):
                note = BASS[bar % 4]
                if i in (6, 14):
                    note = note[0] + str(int(note[1]) + 1)
                m.sfx(sfx.blip(note, 'sine', dur=0.2, glide=1.0), at=t, gain=-8 if full else -14)
        if full and i in STAB and b0 >= 3.5 - 1e-6:
            for n_ in PROG[bar % 4]:
                tmr.add(mallet(n_, 0.5 + 0.1 * (STAB.index(i) % 2), 0.22), t, pan=-0.15 + 0.1 * STAB.index(i))
    bar += 1

# ------------------------------------------------------------------ build 8.0 -> 9.0 into SHOW TIME!!
m.sfx(sfx.riser(1.0, 'hybrid', note='A3', intensity=1.0, end='cut', seed=7), at=HERO, gain=-9)
for k in range(8):                                                       # sixteenth-note clap roll in the last half beat
    tcl.add(drums.clap('tight', 0.45 + 0.07 * k), 8.5 + k * STEP * 1.0)
m.sfx(sfx.punch if hasattr(sfx, 'punch') else sfx.impact('punch', size=1.2), at=HERO, gain=-1) if False else None
m.sfx(sfx.impact('punch', size=1.25), at=HERO, gain=-1)
m.sfx(drums.crash(), at=HERO, gain=-11)
m.sfx(synth.stab(['A3', 'C4', 'E4', 'A4'], 0.45, 0.85, 'dub'), at=HERO, gain=-8)
m.sfx(sfx.boing(0.95, 0.7), at=HERO, gain=-9)

# ------------------------------------------------------------------ cuts, camera, REC
m.sfx(sfx.blip('A5', 'sine', 0.09, glide=1.0), at=0.0, gain=-14)          # REC beep
m.sfx(sfx.click('soft'), at=0.0, gain=-18)
for i, c in enumerate(C['cuts']):
    m.sfx(sfx.shutter('dslr', seed=60 + i), at=c, gain=-8)
    m.sfx(sfx.whoosh(0.3, 'swish', direction=1 if i % 2 else -1, peak=0.5, seed=70 + i), at=c - 0.3 * 0.5, gain=-10)
    m.sfx(sfx.impact('thud', size=0.9), at=c, gain=-8)

# ------------------------------------------------------------------ captions: a pop on every character
for sid in ('s1', 's2', 's3', 's4'):
    sc = SC[sid]
    for li, ln in enumerate(sc['lines']):
        for c, ch in enumerate(ln['text']):
            if ch == ' ':
                continue
            tt = ln['t'] + c * STAG
            if tt < -1e-6:
                continue
            hero_line = (sid == 's3' and li == 1)
            m.sfx(sfx.pop('soft', 0.95 + 0.06 * (c % 8) + 0.1 * li), at=frame(max(tt, 0.0)), gain=-11 if not hero_line else -9,
                  pan=-0.35 + 0.1 * (c % 8))
        # one marimba note per line landing
        note = ['A4', 'C5', 'E5', 'G5'][(li + (hash(sid) % 3)) % 4] if False else ['A4', 'E5'][li]
        tmr.add(mallet(note, 0.8, 0.3), max(ln['t'], 0.0), pan=0.0)
    # notes: bubble pop + arrow scribble
    m.sfx(sfx.pen('pen', 0.45, level=-26), at=sc['arrow_t'], gain=-10, pan=-0.2)
    m.sfx(sfx.pop('bubble', 1.2), at=sc['note']['t'], gain=-10, pan=-0.3)
    # sticker slap
    if 'sticker' in sc:
        m.sfx(sfx.sticker_slap(), at=sc['sticker']['t'], gain=-8, pan=0.4)
        m.sfx(sfx.ding(['E6', 'G6', 'C7', 'A6'][int(sid[1]) - 1]), at=sc['sticker']['t'], gain=-11, pan=0.4)
    for k, st in enumerate(sc['sparkle_t']):
        m.sfx(sfx.shimmer_hit(['G6', 'E6', 'C7'][k]), at=st + 0.03, gain=-14, pan=-0.4 + 0.4 * k)
    # zoom punches
    for p in sc['punches']:
        if p['t'] in C['cuts'] or abs(p['t'] - HERO) < 1e-6 or p['t'] == 0.0:
            continue
        m.sfx(sfx.impact('thud', size=0.5 + 2.0 * p['a']), at=p['t'], gain=-12)
        m.sfx(sfx.swish(0.18, 1, seed=int(p['t'] * 10)), at=p['t'] - 0.1, gain=-17)

# phone clip: upload ticks, hearts, posted chime
m.sfx(sfx.hud_data(0.75, rate=24.0, level=-30), at=SC['s4']['progress'][0], gain=-12)
for k, ht in enumerate(SC['s4']['hearts_t']):
    m.sfx(sfx.pop('bubble', 1.0 + 0.12 * k), at=ht, gain=-10, pan=-0.3 + 0.15 * k)
    tbl.add(fm.bell(['E5', 'G5', 'A5', 'C6', 'E6'][k], 0.3, 0.55, 'glock'), ht, pan=-0.3 + 0.15 * k)
m.sfx(sfx.chime(('C6', 'E6', 'G6'), 0.07, 'celesta'), at=SC['s4']['sticker']['t'], gain=-10)

# ------------------------------------------------------------------ end card
S = FIN['S']
m.sfx(sfx.whoosh(0.55, 'swoosh', direction=-1, peak=0.6, seed=90), at=S - 0.55 * 0.6, gain=-4)
m.sfx(sfx.impact('punch', size=1.0), at=FIN['badge_t'], gain=-2)
m.sfx(sfx.boing(1.25, 0.7), at=FIN['badge_t'], gain=-8)
m.sfx(drums.crash(), at=FIN['badge_t'], gain=-12)
m.sfx(sfx.chime(('A5', 'C6', 'E6', 'A6'), 0.07, 'celesta'), at=FIN['badge_t'] + 0.05, gain=-9)
for c, ch in enumerate(FIN['title']):
    if ch in ' \'':
        continue
    m.sfx(sfx.pop('soft', 1.0 + 0.07 * c), at=frame(FIN['title_t'] + c * STAG), gain=-11, pan=-0.4 + 0.09 * c)
for c, ch in enumerate(FIN['email']):
    t = frame(FIN['email_t'] + c * STAG)
    m.sfx(sfx.pop('soft', 1.0 + 0.04 * (c % 10)), at=t, gain=-12, pan=-0.45 + 0.05 * c)
    tbl.add(fm.bell(['C6', 'D6', 'E6', 'G6', 'A6', 'C7', 'A6', 'G6', 'E6', 'C7'][c % 10], 0.25, 0.5, 'glock'), t, pan=-0.45 + 0.05 * c)
m.sfx(sfx.pop('bubble', 1.1), at=FIN['micro_t'], gain=-11)
m.sfx(sfx.pop('bubble', 1.0), at=FIN['group_t'], gain=-12)
for k, st in enumerate(FIN['sparkle_t']):
    m.sfx(sfx.shimmer_hit(['G6', 'E6', 'C7'][k]), at=st + 0.03, gain=-13, pan=-0.4 + 0.4 * k)
tend = FIN['email_t'] + len(FIN['email']) * STAG
m.sfx(sfx.ding('A6'), at=tend + 0.1, gain=-9, pan=0.2)
m.sfx(synth.stab(['A2', 'E3', 'A3', 'C4', 'E4'], 0.9, 0.8, 'dub'), at=tend + 0.05, gain=-9)
m.sfx(synth.pad(['A3', 'C4', 'E4', 'G4'], DUR - FIN['S'], 0.6, 'warm'), at=FIN['S'], gain=-16)

os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
res = m.export(os.path.join(HERE, 'out', 'audio.wav'), lufs=-14, tp=-1.3, spectrogram=os.path.join(HERE, 'out', 'audio_spec.png'))
m.report()
print({k: res[k] for k in ('duration', 'lufs', 'true_peak', 'warnings') if k in res})
