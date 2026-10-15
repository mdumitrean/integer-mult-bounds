"""mixed: sample joint upgrades of one (5,9) group where members take DIFFERENT optimal hyperplanes (from the 15 common
choices that reach 8,458,352).  3 workers.  usage: mixed.py TOOLKIT INPUTS JOINT.jsonl OUT.jsonl [samples]"""
import os, sys, json, random, multiprocessing as mp, time
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import joint as J
J.INP = sys.argv[2]
if __name__ == '__main__':
    rs = [json.loads(l) for l in open(sys.argv[3]) if l.strip()]; N = int(sys.argv[5]) if len(sys.argv) > 5 else 40
    rnd = random.Random(20261015); T = []
    for label in ('start:619..623', 'start:627..631'):
        good = [r['basis'] for r in rs if r['label'] == label and r['status'] == 'ok' and r['delta'] == 8458352]
        mem = next(r['members'] for r in rs if r['label'] == label)
        for i in range(N):
            combo = [rnd.choice(good) for _ in mem]
            if len({tuple(c) for c in combo}) > 1: T.append((label + ':mixed', mem, combo))
    def run(task):
        label, mem, combo = task; import copy; w = copy.deepcopy(J.BASE); t0 = time.time()
        for q, b in zip(mem, combo): w['start_extra'][str(q)] = b
        try:
            with J.deadline(90): r, g, nc = J.K.solve(w, J.COSTS)
            out = dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - J.BCOST, profile=dict(sorted(r['profile'].items())))
        except J.F.Infeasible: out = dict(status='infeasible')
        except J.Timeout: out = dict(status='timeout')
        out.update(label=label, members=mem, bases=combo, seconds=round(time.time() - t0, 2)); return out
    J.run = run
    with open(sys.argv[4], 'w') as f, mp.get_context('fork').Pool(3, initializer=J.init, maxtasksperchild=40) as pool:
        for r in pool.imap_unordered(run, T): f.write(json.dumps(r, sort_keys=True) + '\n')
    print('done', len(T))
