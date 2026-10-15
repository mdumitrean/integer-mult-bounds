"""gates.py: every gate touching a register, by section, with frames.  usage: gates.py WORD Q [Q...]"""
import gzip, json, sys
w = json.load(gzip.open(sys.argv[1]))
tail = {j: U for j, U in w['early_cleanup']}
for q in map(int, sys.argv[2:]):
    print('== register', q, 'start_extra', w['start_extra'].get(str(q)), 'helper_final', w['helper_final'].get(str(q)))
    for sec in ('precondition', 'A', 'cut', 'B'):
        for i, e in enumerate(w[sec]):
            if q in (e[1:3] if e[0] == 'add' else e[1:2]): print('  ', sec, i, e)
    for i, e in enumerate(w['cleanup']):
        if q in (e[1:3] if e[0] == 'add' else e[1:2]):
            print('  ', 'tail' if i in tail else 'cleanup', i, e[:5], 'tailframe' if i in tail else '', tail.get(i, ''))
