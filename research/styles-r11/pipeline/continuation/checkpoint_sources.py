"""Read-only upstream/overlap checkpoint; all saved material remains inert data.

The gh API query conventions follow scripts/find_overlap.py by Douglas Colkitt
with OpenAI Codex assistance (Apache-2.0). This smaller checkpoint records its
limited search coverage explicitly; it is not a novelty certificate.
"""
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import subprocess

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
OUT = PKG / 'data/continuation-01/checkpoint'
MAIN = 'a7482490b4ca256db67d767a33fa6f7553060807'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = {'recorded_utc': datetime.now(timezone.utc).isoformat(),
               'canonical_main': MAIN, 'files': {}, 'queries': [],
               'scope': 'All open PR titles/bodies; bounded GitHub issue-search queries include closed PRs. Discussion listing is limited to the most recently updated 100 bodies, without comments. No claim of exhaustive historical/code overlap.'}
    def save(name, raw):
        path = OUT / name
        if path.exists():
            raise FileExistsError(path)
        data = gzip.compress(raw, mtime=0) if name.endswith('.gz') else raw
        path.write_bytes(data)
        receipt['files'][name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                                  'uncompressed_sha256': hashlib.sha256(raw).hexdigest()}
    for name in ('AGENTS.md', 'autoresearch.md', 'docs/research/agent-task-catalog.json',
                 'docs/research/research-family-status.md', 'certificates/selected-result.json'):
        raw = subprocess.check_output(['git', 'show', MAIN + ':' + name], cwd=ROOT)
        save(name.replace('/', '__') + '.gz', raw)
    def gh(args, payload=None):
        value = subprocess.run(['gh', 'api', *args], input=json.dumps(payload) if payload else None,
                               text=True, capture_output=True, timeout=90, check=True)
        return value.stdout
    try:
        raw = gh(['repos/CrocSwap/integer-mult-bounds/pulls?state=open&per_page=100',
                  '--paginate', '--jq', '@json'])
        rows = [p for line in raw.splitlines() for p in json.loads(line)]
        selected = [{k: p.get(k) for k in ('number', 'title', 'body', 'html_url', 'updated_at', 'draft', 'state')}
                    | {'head': p['head']['sha'], 'author': p['user']['login']} for p in rows]
        save('open-prs.json.gz', json.dumps(selected, sort_keys=True).encode())
        receipt['open_pr_count'] = len(selected)
        terms = ('sandpile', 'L-system', 'lsystem', '2853', '2833', 'fill', 'kernel')
        receipt['open_matches'] = [{k: p[k] for k in ('number', 'title', 'head', 'html_url')}
                                   for p in selected if any(t.lower() in (p['title'] + ' ' + (p['body'] or '')).lower()
                                                           for t in terms)]
    except (subprocess.SubprocessError, ValueError, KeyError) as exc:
        receipt['open_pr_error'] = type(exc).__name__ + ': ' + str(exc)[:500]
    for term in ('"2853"', '"2833"', '"sandpile"', '"L-system"'):
        query = 'repo:CrocSwap/integer-mult-bounds is:pr ' + term
        try:
            result = json.loads(gh(['search/issues', '-X', 'GET', '-f', 'q=' + query, '-f', 'per_page=100']))
            name = 'search-' + term.strip('"').lower() + '.json.gz'
            save(name, json.dumps(result, sort_keys=True).encode())
            receipt['queries'].append({'query': query, 'total_count': result['total_count'],
                                       'returned': len(result['items']), 'incomplete_results': result['incomplete_results'], 'file': name})
        except (subprocess.SubprocessError, ValueError, KeyError) as exc:
            receipt['queries'].append({'query': query, 'error': type(exc).__name__ + ': ' + str(exc)[:500]})
    query = '''query { repository(owner:"CrocSwap",name:"integer-mult-bounds") {
      discussions(first:100,orderBy:{field:UPDATED_AT,direction:DESC}) {
        pageInfo {hasNextPage endCursor} nodes {number title body url updatedAt}
      }
    }}'''
    try:
        result = json.loads(gh(['graphql', '--input', '-'], {'query': query}))
        save('recent-discussions.json.gz', json.dumps(result, sort_keys=True).encode())
        connection = result['data']['repository']['discussions']
        receipt['discussion_count'] = len(connection['nodes'])
        receipt['discussion_has_more'] = connection['pageInfo']['hasNextPage']
    except (subprocess.SubprocessError, ValueError, KeyError) as exc:
        receipt['discussion_error'] = type(exc).__name__ + ': ' + str(exc)[:500]
    save('RECEIPT.json', (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode())
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('files', 'open_matches')}, indent=2))


if __name__ == '__main__':
    main()
