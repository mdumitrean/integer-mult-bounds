"""Shared pattern-relaxation core (import-safe)."""
import json, os
W = (4, 5, 7, 8, 9); NB = {8: 49728, 16: 33152, 32: 33152, 48: 33152}
UP = 8458352   # extra word over base word, per call (4 upgrades); r4 D-widths
c = {int(k): v for k, v in json.load(open(os.path.join(os.path.dirname(__file__), '..', 'out', 'COSTS.json')))['c'].items()}; c[0] = 0
CUR = 417 * UP + 22748 * c[48]
def pats(cap, widths=W):
    out = []
    def rec(rem, start, cur):
        out.append((tuple(cur), rem))
        for i in range(start, len(widths)):
            if widths[i] <= rem: rec(rem - widths[i], i, cur + [widths[i]])
    rec(cap, 0, []); return out
