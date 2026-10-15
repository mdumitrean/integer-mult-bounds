import gzip, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))      # .../scratchpad
R3 = os.path.join(SCR, 'r3'); TK = os.path.join(R3, 'toolkit-rev3'); OUT = os.path.join(HERE, '..', 'out')
sys.path.insert(0, TK)
os.environ.setdefault('IMB_ROOT', os.path.join(R3, 'main')); os.environ.setdefault('IMB_B', '0.001679754956125544')
WORDS = dict(base=os.path.join(R3, 'inputs', 'gauge44-word-566-554.json.gz'), extra=os.path.join(R3, 'inputs', 'extra-word-566-554.json.gz'))
CALLS = dict(base=249, extra=417)
V = 112
def load(name): return json.load(gzip.open(WORDS[name]))
def rel(p): return os.path.relpath(os.path.abspath(p), SCR)
