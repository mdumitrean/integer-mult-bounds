"""Read-only source overlap checkpoint for continuation03.

REST/GraphQL query conventions follow Douglas Colkitt's find_overlap helper
(Apache-2.0); this is a separate acquisition implementation. Fetched bodies,
comments and any quoted source code remain inert data. No science is run.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import re
import subprocess
import time

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
MAIN = '318ba71b8927f81141f41a89c1af74323586f253'
REPOSITORY = 'CrocSwap/integer-mult-bounds'
OUT = PKG / 'data/continuation-03/checkpoint'
HTTP_TIMEOUT = 45
TOTAL_SECONDS = 1200
MAX_PAGES = 100
STRONG_TERMS = ('sandpile', 'toppling', 'laplacian', 'l-system', 'l system',
                'lindenmayer', 'parikh', 'smith normal', 'critical group',
                'odometer', 'abelian network')
SUPPORT_TERMS = ('paired', 'packing', 'shared-kernel', 'shared kernel',
                 'normal45', 'normal 45', 'joint kernel', '2930', '2942', '2917')
HUBS = (1163, 1166, 1167, 2612)
KNOWN_PRS = (2917, 2918, 2930, 2932, 2942, 2943)


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


class Acquisition:
    def __init__(self, output):
        self.output = Path(output)
        if self.output.exists():
            raise FileExistsError('immutable checkpoint already exists')
        self.output.mkdir(parents=True)
        self.start = time.monotonic()
        pins = PKG / 'data/continuation-03/guidance/PINS.json'
        self.receipt = dict(schema_version=1, repository=REPOSITORY, canonical_main=MAIN,
            started_utc=utc(), files={}, remote={}, errors=[],
            script_sha256=digest(Path(__file__).read_bytes()),
            guidance=dict(path=str(pins.relative_to(PKG)), sha256=digest(pins.read_bytes())),
            scope='Read-only source and overlap acquisition. No scientific experiment or fetched-code execution.',
            limits=[
                'Each paginated connection is sampled over time, not atomically. Updated-order pagination can move records during acquisition; page and unique counts are retained.',
                'All open and closed PR title/body pages and all discussion body pages are requested until exhausted, subject to100pages/connection and1200seconds overall. Completeness is explicit.',
                'Selected structural, paired and packing discussions receive all available comments and replies; nonselected discussion comments are not searched.',
                'Selected PRs receive all available issue comments, review summaries and inline review comments. File patches, arbitrary linked repositories and unpublished local work are not acquired.',
                'Metadata claims and archival merges are not independent mathematical validation. A keyword miss is not a novelty or nonoverlap proof.'])
        self.prs, self.discussions = {}, {}

    def save(self, name, value, source):
        raw = encoded(value)
        data = gzip.compress(raw, mtime=0) if name.endswith('.gz') else raw
        target = self.output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(data)
        self.receipt['files'][name] = dict(sha256=digest(data), bytes=len(data),
            uncompressed_sha256=digest(raw), source=source)

    def gh(self, args, payload=None):
        if time.monotonic() - self.start >= TOTAL_SECONDS:
            raise TimeoutError('checkpoint wall budget exhausted')
        result = subprocess.run(['gh', 'api', *args], cwd=ROOT,
            input=json.dumps(payload) if payload is not None else None,
            text=True, capture_output=True, timeout=HTTP_TIMEOUT)
        if result.returncode:
            raise RuntimeError('read-only GitHub request failed: exit' + str(result.returncode))
        value = json.loads(result.stdout)
        if isinstance(value, dict) and value.get('errors'):
            raise RuntimeError('GitHub GraphQL returned errors')
        return value

    def graphql(self, query, variables):
        return self.gh(['graphql', '--input', '-'], dict(query=query, variables=variables))

    def rest_pages(self, endpoint, fields=None):
        rows, pages, complete, error = [], 0, False, None
        started = utc()
        try:
            for page in range(1, MAX_PAGES + 1):
                join = '&' if '?' in endpoint else '?'
                batch = self.gh([endpoint + join + 'per_page=100&page=' + str(page)])
                if not isinstance(batch, list):
                    raise ValueError('expected REST list')
                pages += 1
                rows.extend(fields(row) if fields else row for row in batch)
                if len(batch) < 100:
                    complete = True
                    break
        except (subprocess.SubprocessError, ValueError, RuntimeError, KeyError, TimeoutError) as exc:
            error = type(exc).__name__ + ': ' + str(exc)[:240]
        return rows, dict(pages=pages, rows=len(rows), complete=complete, error=error,
                          started_utc=started, finished_utc=utc())

    def pull_requests(self):
        def fields(p):
            return {k: p.get(k) for k in ('number', 'title', 'body', 'html_url', 'updated_at',
                'created_at', 'closed_at', 'merged_at', 'draft', 'state')} | dict(
                head=p['head']['sha'], author=p['user']['login'], base=p['base']['sha'])
        for state in ('open', 'closed'):
            endpoint = f'repos/{REPOSITORY}/pulls?state={state}&sort=updated&direction=desc'
            rows, coverage = self.rest_pages(endpoint, fields)
            self.save(state + '-prs.json.gz', rows, dict(kind='REST', endpoint=endpoint))
            coverage['unique_numbers'] = len({row['number'] for row in rows})
            self.receipt['remote'][state + '_prs'] = coverage
            for row in rows:
                old = self.prs.get(row['number'])
                if old is None or row['updated_at'] > old['updated_at']:
                    self.prs[row['number']] = row
            print(json.dumps(dict(phase='pulls', state=state, **coverage)), flush=True)
        matches = self.index(self.prs.values())
        self.save('pr-overlap-index.json.gz', matches, dict(kind='local-inert-text-index', terms=STRONG_TERMS + SUPPORT_TERMS))
        self.receipt['distinct_prs'] = len(self.prs)
        print(json.dumps(dict(phase='priority-prs', rows=sorted(matches, key=lambda p:p['updated_at'], reverse=True)[:20])), flush=True)

    @staticmethod
    def index(rows):
        matches = []
        for row in rows:
            text = (row['title'] + '\n' + (row.get('body') or '')).lower()
            terms = [term for term in STRONG_TERMS + SUPPORT_TERMS if term in text]
            if terms:
                matches.append({k: row[k] for k in ('number', 'title', 'head', 'author', 'html_url', 'state', 'updated_at') if k in row}
                    | dict(terms=terms, decimal_tokens=sorted(set(re.findall(r'0\.001[0-9]{6,}', text)))))
        return sorted(matches, key=lambda row:row['number'])

    def discussion_bodies(self):
        query = '''query($cursor:String) { repository(owner:"CrocSwap",name:"integer-mult-bounds") {
          discussions(first:100,after:$cursor,orderBy:{field:UPDATED_AT,direction:DESC}) {
            totalCount pageInfo {hasNextPage endCursor}
            nodes {id number title body url updatedAt createdAt author {login}}
          }
        }}'''
        rows, cursor, pages, complete, error, total = [], None, 0, False, None, None
        started = utc()
        try:
            for page in range(1, MAX_PAGES + 1):
                conn = self.graphql(query, {'cursor':cursor})['data']['repository']['discussions']
                total = conn['totalCount']; pages += 1; rows.extend(conn['nodes'])
                print(json.dumps(dict(phase='discussion-bodies', page=page, rows=len(rows), reported_total=total)), flush=True)
                if not conn['pageInfo']['hasNextPage']:
                    complete = True
                    break
                cursor = conn['pageInfo']['endCursor']
        except (subprocess.SubprocessError, ValueError, RuntimeError, KeyError, TimeoutError) as exc:
            error = type(exc).__name__ + ': ' + str(exc)[:240]
        for row in rows:
            old = self.discussions.get(row['number'])
            if old is None or row['updatedAt'] > old['updatedAt']:
                self.discussions[row['number']] = row
        self.save('discussions.json.gz', rows, dict(kind='GraphQL', query=query))
        coverage = dict(pages=pages, rows=len(rows), unique_numbers=len(self.discussions), reported_total=total,
            complete=complete, error=error, started_utc=started, finished_utc=utc())
        self.receipt['remote']['discussion_bodies'] = coverage
        print(json.dumps(dict(phase='discussion-bodies-complete', **coverage)), flush=True)

    def discussion_thread(self, number):
        query = '''query($number:Int!,$cursor:String) { repository(owner:"CrocSwap",name:"integer-mult-bounds") {
          discussion(number:$number) {id number title body url updatedAt author {login}
            comments(first:100,after:$cursor) {totalCount pageInfo {hasNextPage endCursor}
              nodes {id databaseId body url createdAt updatedAt author {login}
                replies(first:100) {totalCount pageInfo {hasNextPage endCursor}
                  nodes {id databaseId body url createdAt updatedAt author {login}}}
              }
            }
          }
        }}'''
        replies_query = '''query($id:ID!,$cursor:String) { node(id:$id) { ... on DiscussionComment {
          replies(first:100,after:$cursor) {totalCount pageInfo {hasNextPage endCursor}
            nodes {id databaseId body url createdAt updatedAt author {login}}}
        }}}'''
        comments, cursor, pages, complete, error, total, body = [], None, 0, False, None, None, None
        started = utc(); reply_pages = 0; incomplete_replies = []
        try:
            for page in range(1, MAX_PAGES + 1):
                body = self.graphql(query, dict(number=number, cursor=cursor))['data']['repository']['discussion']
                if body is None:
                    raise ValueError('discussion absent')
                conn = body['comments']; pages += 1; total = conn['totalCount']
                for comment in conn['nodes']:
                    replies = comment['replies']; reply_rows = list(replies['nodes']); used = 1
                    while replies['pageInfo']['hasNextPage'] and used < MAX_PAGES:
                        replies = self.graphql(replies_query, dict(id=comment['id'], cursor=replies['pageInfo']['endCursor']))['data']['node']['replies']
                        reply_rows.extend(replies['nodes']); used += 1; reply_pages += 1
                    comment['replies'] = dict(nodes=reply_rows, totalCount=replies['totalCount'],
                        complete=not replies['pageInfo']['hasNextPage'], pages=used)
                    if not comment['replies']['complete']:
                        incomplete_replies.append(comment['id'])
                    comments.append(comment)
                if not conn['pageInfo']['hasNextPage']:
                    complete = True
                    break
                cursor = conn['pageInfo']['endCursor']
        except (subprocess.SubprocessError, ValueError, RuntimeError, KeyError, TimeoutError) as exc:
            error = type(exc).__name__ + ': ' + str(exc)[:240]
        if body:
            body['comments'] = dict(nodes=comments, totalCount=total, complete=complete)
        coverage = dict(pages=pages, comments=len(comments), unique_comments=len({x['id'] for x in comments}),
            reported_comments=total, complete=complete and not incomplete_replies and error is None,
            replies=sum(len(x['replies']['nodes']) for x in comments), extra_reply_pages=reply_pages,
            incomplete_reply_threads=incomplete_replies, error=error, started_utc=started, finished_utc=utc())
        self.save(f'threads/discussion-{number}.json.gz', dict(discussion=body, coverage=coverage),
            dict(kind='GraphQL', comments_query=query, replies_query=replies_query, number=number))
        self.receipt['remote']['discussion_' + str(number)] = coverage
        print(json.dumps(dict(phase='discussion-thread', number=number, **coverage)), flush=True)

    def selected_threads(self):
        selected = {}
        for number, row in self.discussions.items():
            text = (row['title'] + '\n' + row['body']).lower()
            terms = [term for term in STRONG_TERMS + SUPPORT_TERMS if term in text]
            if terms:
                selected[number] = terms
        for number in HUBS:
            selected.setdefault(number, []).append('required-hub-or-paired-thread')
        ordered = sorted(selected, key=lambda n:(n not in HUBS, not any(t in STRONG_TERMS for t in selected[n]),
            -(int(self.discussions.get(n, {}).get('updatedAt', '2000')[:4])), -n))
        self.save('selected-discussion-threads.json.gz', [dict(number=n, reasons=selected[n]) for n in ordered],
            dict(kind='deterministic-inert-metadata-selection', terms=STRONG_TERMS + SUPPORT_TERMS, required=HUBS))
        self.receipt['selected_discussion_threads'] = ordered
        for number in ordered:
            if time.monotonic() - self.start >= TOTAL_SECONDS:
                self.receipt['errors'].append(dict(kind='unvisited_discussion', number=number, reason='wall-time limit'))
                continue
            self.discussion_thread(number)

    def selected_pr_comments(self):
        strong = set()
        support_recent = []
        for number, row in self.prs.items():
            text = (row['title'] + '\n' + (row['body'] or '')).lower()
            if any(term in text for term in STRONG_TERMS):
                strong.add(number)
            if any(term in text for term in SUPPORT_TERMS):
                support_recent.append(row)
        latest = [p['number'] for p in sorted(support_recent, key=lambda p:p['updated_at'], reverse=True)[:20]]
        selected = sorted(strong | set(latest) | set(KNOWN_PRS), reverse=True)
        self.receipt['selected_pr_threads'] = dict(numbers=selected,
            rule='All PR body/title matches for structural terms, twenty most recently updated supporting matches, and six named source/obstruction PRs.')
        for number in selected:
            result = dict(number=number, head=self.prs.get(number, {}).get('head'), author=self.prs.get(number, {}).get('author'))
            for name, endpoint in [('issue_comments', f'repos/{REPOSITORY}/issues/{number}/comments'),
                                   ('reviews', f'repos/{REPOSITORY}/pulls/{number}/reviews'),
                                   ('review_comments', f'repos/{REPOSITORY}/pulls/{number}/comments')]:
                rows, coverage = self.rest_pages(endpoint)
                result[name] = dict(rows=rows, coverage=coverage)
            self.save(f'threads/pr-{number}.json.gz', result, dict(kind='REST', number=number))
            self.receipt['remote']['pr_' + str(number)] = {k:result[k]['coverage'] for k in ('issue_comments','reviews','review_comments')}
            print(json.dumps(dict(phase='pr-thread', number=number,
                comments=sum(len(result[k]['rows']) for k in ('issue_comments','reviews','review_comments')))), flush=True)
            if time.monotonic() - self.start >= TOTAL_SECONDS:
                break

    def finish(self):
        self.receipt['finished_utc'] = utc()
        self.receipt['elapsed_seconds'] = time.monotonic() - self.start
        raw = (json.dumps(self.receipt, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
        with (self.output / 'RECEIPT.json').open('xb') as handle:
            handle.write(raw)
        print(json.dumps(dict(phase='complete', path=str((self.output/'RECEIPT.json').relative_to(PKG)),
            sha256=digest(raw), files=len(self.receipt['files']), errors=self.receipt['errors'],
            elapsed_seconds=self.receipt['elapsed_seconds'])), flush=True)

    def run(self):
        try:
            self.pull_requests()
            self.discussion_bodies()
            self.selected_threads()
            self.selected_pr_comments()
        finally:
            self.finish()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    if args.output.resolve() != OUT.resolve():
        parser.error('this frozen acquisition writes only data/continuation-03/checkpoint')
    Acquisition(args.output).run()
