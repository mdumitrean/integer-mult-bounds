import gzip, json, os, sys
R = 'r3'
TK = R + '/toolkit-rev3'
sys.path.insert(0, TK)
os.environ.setdefault('IMB_ROOT', R + '/main')
os.environ.setdefault('IMB_B', '0.001679754956125544')
WORDS = dict(base=R + '/inputs/gauge44-word-566-554.json.gz', extra=R + '/inputs/extra-word-566-554.json.gz')
CALLS = dict(base=249, extra=417)
def load(name): return json.load(gzip.open(WORDS[name]))
V = 112
def cls(r): return 'D' if r < V else ('P' if r < 2 * V else 'H')
def regs(e): return e[1:3] if e[0] == 'add' else e[1:2]
