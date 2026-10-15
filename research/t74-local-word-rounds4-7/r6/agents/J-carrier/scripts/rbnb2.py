"""rbnb2: rbnb with both segment-start and segment-latest positions as candidates (position sensitivity).  usage: rbnb2.py WORD q"""
import sys, os
JDIR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, JDIR)
import jcommon
orig = jcommon.Pivot.candidates
def both(self):
    b = orig(self); return sorted(set(b) | set(jcommon.candidates_latest(self, b)))
jcommon.Pivot.candidates = both
import rbnb
if __name__ == '__main__':
    wname = sys.argv[1]
    for q in map(int, sys.argv[2:]):
        rbnb.solve(wname, q)
        D = os.path.join(JDIR, '..', 'out'); os.replace(f'{D}/RBNB-{wname}-{q}.json', f'{D}/RBNB2-{wname}-{q}.json')
