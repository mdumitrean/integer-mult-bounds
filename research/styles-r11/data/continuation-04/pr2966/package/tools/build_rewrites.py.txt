#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Append the declared fourteen-rewrite stage to PR2942's normal-45 overlay (PR2917 source + four paired extractions).

Rewrites (R-retime, A3779-cut-start-read, PM-carrier-lender-entry, B-carrier-retime, A-commuting-swap) by Jeremy Kothe (jeremykothe2), with AI
assistance, on mdumitrean's PR2942 words (mason-hale's PR2917 words plus four normal-45 extractions). Overlay/rebuild conventions are credited to
PR2942 (mdumitrean), PR2908 (jeremydiviney) and PR2917 (mason-hale).
"""
import argparse, gzip, hashlib, json, shutil
from pathlib import Path

PARENT = '79956f19c5c3d4d1ad3578e4b3d6844bc54c1f3680825fc87c80cc04f069dae8'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    b = p.read_bytes(); return json.loads(gzip.decompress(b) if p.suffix == '.gz' else b)
def save(p, x): p.write_text(json.dumps(x, indent=2, sort_keys=True) + '\n')
def tree(p):
    assert not any(f.is_symlink() for f in p.rglob('*'))
    return {f.relative_to(p).as_posix(): sha(f) for f in sorted(p.rglob('*')) if f.is_file() and f != p / 'MANIFEST.json'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--local-package', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    src, out, p = a.source.resolve(), a.out.resolve(), a.local_package.resolve()
    assert __debug__ and not out.exists() and not out.is_relative_to(src)
    assert sha(src / 'MANIFEST.json') == PARENT and tree(src) == read(src / 'MANIFEST.json')
    pins = read(p / 'REWRITE-PINS.json')
    assert all(sha(p / n) == h for n, h in pins.items())
    shutil.copytree(src, out)
    local = out / 'new/borrow/rewrites'
    local.mkdir()
    for n in pins:
        shutil.copy2(p / n, local / Path(n).name)
    shutil.copy2(p / 'rewrite/declared_rewrites.py', out / 'new/borrow/declared_rewrites.py')
    shutil.copy2(p / 'rewrite/rewrites_review.py', out / 'new/borrow/rewrites_review.py')
    providers = read(src / 'new/BORROW-PROVIDERS.json')
    records = {}
    for tag, pid in [('base', 'gauge44'), ('extra', 'extra')]:
        q = out / f'new/borrow/words/BORROW-WORD-43{tag}.json.gz'
        assert read(q) == read(p / f'data/WORD-{tag}.json.gz'), 'overlay word is the PR2942 word'
        shutil.copy2(q, out / f'new/borrow/inputs/NORMAL45-WORD-{tag}.json.gz')
        shutil.copy2(p / f'rewrite/FINAL-WORD-{tag}.json.gz', q)
        word = read(q)
        assert providers[pid]['widths'] == [len(word['helper_final'].get(str(h), [0] * 9)) - len(word['start_extra'].get(str(h), []))
                                           for h in sorted(set(range(224, 704)) - set(word['removed']))], 'helper widths unchanged'
        providers[pid]['actual_paid_profile'] = word['report']['local_profile']
        records[tag] = {'parent_sha256': sha(p / f'data/WORD-{tag}.json.gz'), 'word_sha256': sha(q)}
    save(out / 'new/BORROW-PROVIDERS.json', providers)
    path = out / 'new/rebuild_borrow.py'
    text = path.read_text()
    anchor = "    final=json.loads(gzip.decompress(shipped.read_bytes()))"
    assert text.count(anchor) == 1
    block = """    # Declared fourteen rewrites (five classes) on PR2942's normal-45 word; widths, buffers and compensation are unchanged.
    import declared_rewrites
    rewrite_parent=json.loads(gzip.decompress((D/'inputs'/f'NORMAL45-WORD-{wt}.json.gz').read_bytes()))
    assert chain[-1]==rewrite_parent
    rewrite_word,_=declared_rewrites.apply(chain[-1],json.loads((D/'rewrites/REWRITES.json').read_text()))
    chain.append(rewrite_word);steps.append('declared-fourteen-rewrites')
"""
    path.write_text(text.replace(anchor, block + anchor))
    path = out / 'verify.py'
    text = path.read_text()
    line = next(s for s in text.splitlines() if s.startswith("run('paired-extension-review'"))
    assert text.count(line) == 1
    review = ("run('declared-rewrite-review',P/'new/borrow/rewrites_review.py','--source-dir',P/'new/borrow',"
              "'--parent-base',P/'new/borrow/inputs/NORMAL45-WORD-base.json.gz','--parent-extra',P/'new/borrow/inputs/NORMAL45-WORD-extra.json.gz',"
              "'--candidate-base',P/'new/borrow/words/BORROW-WORD-43base.json.gz','--candidate-extra',P/'new/borrow/words/BORROW-WORD-43extra.json.gz',"
              "'--rewrites',P/'new/borrow/rewrites/REWRITES.json','--out-dir',work/'declared-rewrite-review')")
    path.write_text(text.replace(line, line + "\n" + review))
    before, after = tree(src), tree(out)
    changes = {n: {'before': before.get(n), 'after': after.get(n)} for n in set(before) | set(after) if before.get(n) != after.get(n)}
    expected = {'new/BORROW-PROVIDERS.json', 'new/rebuild_borrow.py', 'verify.py', 'new/borrow/declared_rewrites.py', 'new/borrow/rewrites_review.py'}
    expected |= {f'new/borrow/words/BORROW-WORD-43{tag}.json.gz' for tag in ('base', 'extra')}
    expected |= {f'new/borrow/inputs/NORMAL45-WORD-{tag}.json.gz' for tag in ('base', 'extra')}
    expected |= {'new/borrow/rewrites/' + Path(n).name for n in pins}
    assert set(changes) == expected and tree(src) == before
    save(out / 'MANIFEST.json', after)
    result = {'status': 'PASS_SOURCE_BOUND_DECLARED_REWRITE_OVERLAY', 'parent_manifest_sha256': PARENT, 'manifest_sha256': sha(out / 'MANIFEST.json'),
              'source_file_count': len(after), 'changes': changes, 'words': records, 'builder_sha256': sha(Path(__file__))}
    save(out.parent / (out.name + '-DERIVATION.json'), result)
    print(result['status'], result['manifest_sha256'], len(after), flush=True)


if __name__ == '__main__':
    main()
