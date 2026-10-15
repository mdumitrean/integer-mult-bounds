"""vleaver.py: the k8 leaver cell-word pipeline (reproduce_leaver.py steps 1-5: gauge-forward, port0-3, regroup, HPE,
cold44) for a FACTORY VARIANT given by an XPARAM file (cgx_leaver.py's 'exch' and 'prio' keys), without pins; then the
exact target-response analysis (resp.py).  Adapted from LeaverSAT's construction/leaver/reproduce_leaver.py (Apache-2.0).
usage: vleaver.py --src SRC --word-dir WD --xparam XP.json --out OUT [--pairing-ranks JSON]"""
import argparse, gzip, hashlib, importlib.util, json, os, shutil, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import resp
def read(p):
    raw = Path(p).read_bytes(); return json.loads(gzip.decompress(raw) if str(p).endswith('.gz') else raw)
def enc(x): return json.dumps(x, sort_keys=True, separators=(',', ':')).encode()
def dump(p, v): p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(gzip.compress(enc(v), mtime=0))
def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, required=True); ap.add_argument('--word-dir', type=Path, required=True)
    ap.add_argument('--xparam', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--pairing-ranks'); ap.add_argument('--id', default='k8'); a = ap.parse_args()
    out = a.out.resolve(); assert not out.exists(); out.mkdir(parents=True)
    SRC = a.src.resolve(); HERE = SRC / 'delta/gauge44-slots/construction/leaver'; NOTRI = HERE.parent / 'notri'
    up = SRC / 'pr635/research/complex-571-cold14-st2'; src = SRC / 'main17/research/complex-k492-owner-repair/vendor/multicold'
    base = src / 'vendor/pr558'; parent = base / 'vendor/pr552'; gk = parent / 'complex-local/static44/gk'
    structural = SRC / 'main17/research/structural-gain/frontier-composition'; wd = a.word_dir.resolve()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTHONINTMAXSTRDIGITS='0', MULTICOLD_SOURCE=str(src), GAIN_PR564_SOURCE=str(src))
    for k in ('PYTHONOPTIMIZE', 'XPARAM', 'EXTRAH', 'PAIRING_RANKS', 'DIAG', 'HYBBUDGET'): env.pop(k, None)
    res = dict(xparam=str(a.xparam), stage=None)
    def run(label, script, *args):
        with (out / (label + '.log')).open('w') as f:
            rc = subprocess.call([sys.executable, '-B', str(src / 'code/run_portable.py'), str(script), *map(str, args)], env=env, stdout=f, stderr=subprocess.STDOUT, timeout=600)
        if rc: res['stage'] = 'FAIL:' + label; res['log_tail'] = (out / (label + '.log')).read_text()[-600:]; raise SystemExit
    try:
        shutil.copy(HERE / ('TRI-LEAVER-%s.json' % a.id), out / 'TRI.json'); shutil.copy(HERE / ('CODED-CELLS-%s.json' % a.id), out / 'CODED-CELLS.json')
        env['XPARAM'] = str(a.xparam.resolve()); raw = out / 'raw'
        run('gauge-forward', HERE / 'cgx_leaver.py', wd / 'hamming', raw, out / 'TRI.json')
        word = raw / 'FULL-WORD.json.gz'; res['raw_sha256'] = hashlib.sha256(enc(read(word))).hexdigest()
        chain = [parent / 'complex-local/static44/inputs/RAW504.json.gz', structural / 'global-replay/base/split-centres/FULL-WORD.json.gz',
                 wd / 'shadow-early/FULL-WORD.json.gz', structural / 'multicold-eight-word/FULL-WORD.json.gz', wd / 'shadow-prefix/FULL-WORD.json.gz']
        for i, (b, c) in enumerate(zip(chain, chain[1:])):
            t = out / ('port%d' % i)
            run('port%d' % i, NOTRI / 'port_stage_x.py', '--shadow-input', b, '--shadow-output', c, '--input', word, '--map', raw / 'HELPER-MAP.json', '--gk-dir', gk, '--out', t)
            word = t / 'FULL-WORD.json.gz'
        w = read(word); rg = {json.dumps(c['before']): c['after'] for c in read(HERE / ('REGROUP-LEAVER-%s.json' % a.id))['changes']}
        n = 0
        for part in ('A', 'B'):
            for i, e in enumerate(w[part]):
                k = json.dumps(e)
                if k in rg: w[part][i] = rg[k]; n += 1
        sys.path.insert(0, str(gk)); import gk_word as GW, gk_common as GC
        GW.V = GC.V = 112; GW.DATA = GC.DATA = 7168
        H = GW.profile(w); w['report'].update(local_profile={str(k): z for k, z in sorted(H.items()) if z}, local_rank_mass=sum(r * z for r, z in H.items()))
        res['regroup_count'] = n; dump(out / 'regroup/FULL-WORD.json.gz', w)
        h = load('upstream_hpe', up / 'code/build_hpe.py'); used, ch = set(), []
        for c in h.candidates(w):
            rs = set(h.regs(w['cleanup'][c['cleanup_index']]))
            if rs & used: continue
            used |= rs; ch.append(c)
        res['hpe_changes'] = len(ch); w = h.apply(w, ch); dump(out / 'hpe/FULL-WORD.json.gz', w)
        hm = set(read(raw / 'HELPER-MAP.json')['map'].values())
        env['EXTRAH'] = json.dumps(sorted(set(range(224, 224 + w['report']['R'])) - hm))
        if a.pairing_ranks: env['PAIRING_RANKS'] = a.pairing_ranks
        run('cold44', NOTRI / 'cold44x.py', '--input', out / 'hpe/FULL-WORD.json.gz', '--out', out / 'cold44', '--hamming', wd / 'hamming', '--upstream-package', up)
        res['pairing_ranks'] = [b['pairing_rank'] for b in read(out / 'cold44/CONSTRUCTION.json')['blocks']]
        w = read(out / 'cold44/FULL-WORD.json.gz'); res['cold44_sha256'] = hashlib.sha256(enc(w)).hexdigest()
        rep = w['report']; res.update(R=rep['R'], local_profile=rep['local_profile'], width_inventory=rep.get('width_inventory'))
        r = resp.analyse(w); res.update({k: r[k] for k in ('n_read', 'read', 'entering', 'ended', 'entering_with_response', 'ended_with_response')})
        res['stage'] = 'OK'
    except SystemExit: pass
    except Exception as e: res['stage'] = 'ERROR:' + repr(e)[:300]
    (out / 'RESULT.json').write_text(json.dumps(res)); print(json.dumps({k: res.get(k) for k in ('stage', 'n_read', 'pairing_ranks', 'cold44_sha256')}))
if __name__ == '__main__': main()
