"""batch.py: run vleaver.py on a list of XPARAM variants with <= W concurrent subprocesses (each with a timeout);
summarise new zero-response helpers vs the baseline.  usage: batch.py JOBS.json OUTDIR W"""
import json, subprocess, sys, os, time, resource
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
U = Path(__file__).resolve().parents[1]; S = U.parents[2]; T = S / 'r7/agents/T-generator'
jobs = json.load(open(sys.argv[1])); od = Path(sys.argv[2]); od.mkdir(parents=True, exist_ok=True); W = int(sys.argv[3])
def one(j):
    xp = od / ('XP-%s.json' % j['id']); xp.write_text(json.dumps(j['xparam']))
    out = od / ('v-%s' % j['id'])
    if (out / 'RESULT.json').exists(): return
    try:
        subprocess.run([sys.executable, '-B', str(U / 'scripts/vleaver.py'), '--src', str(U / 'src'), '--word-dir', str(T / 'out/repro-word'),
                        '--xparam', str(xp), '--out', str(out)], timeout=900, capture_output=True)
    except subprocess.TimeoutExpired:
        out.mkdir(exist_ok=True); (out / 'RESULT.json').write_text(json.dumps(dict(stage='TIMEOUT')))
t0 = time.time()
with ThreadPoolExecutor(W) as ex: list(ex.map(one, jobs))
print('done', len(jobs), 'jobs in', round(time.time() - t0), 's; children maxrss MB', resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 2**20)
