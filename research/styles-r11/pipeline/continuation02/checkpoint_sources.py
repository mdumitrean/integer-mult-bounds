"""Read-only continuation-02 upstream checkpoint; fetched text is inert data.

REST/GraphQL coverage follows the query conventions in Douglas Colkitt's
scripts/find_overlap.py (Apache-2.0; credited OpenAI Codex assistance). This
independent acquisition script never imports or executes that fetched helper.
No claim of novelty or scientific validation follows from these text matches.
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
MAIN = '914cd73f563acaaa682d733a9fbfcc07272336a3'
REPOSITORY = 'CrocSwap/integer-mult-bounds'
OUT = PKG/'data/continuation-02/checkpoint'
MAX_PAGES = 40
HTTP_TIMEOUT = 25
TOTAL_SECONDS = 300
GUIDANCE = (
    'AGENTS.md', 'CONTRIBUTING.md', 'autoresearch.md',
    'docs/research/agent-task-catalog.json',
    'docs/research/research-priority-log.md',
    'docs/research/research-family-status.md',
    'docs/research/current-status.md',
    'docs/research/contribution-review.md',
    'docs/research/pr-ledger.md',
    'certificates/selected-result.json',
    'scripts/find_overlap.py',
)
TERMS = ('cross-call', 'cross call', 'simultaneous', 'iterated', 'iterative',
         'multi-exchange', 'multi exchange', 'fill exchange', 'two-role',
         '2917', 'styles-r11', 'continuation-01', 'paired helper', 'helper408')


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def main(output=OUT):
    start = time.monotonic()
    output = Path(output)
    if output.exists():
        raise FileExistsError('immutable checkpoint already exists: '+str(output))
    output.mkdir(parents=True)
    receipt = dict(schema_version=1,recorded_utc=utc(),canonical_main=MAIN,
                   repository=REPOSITORY,files={},guidance=[],remote={},errors=[],
                   script_sha256=digest(Path(__file__).read_bytes()),
                   scope='Metadata/text overlap only; no scientific experiments or fetched-code execution.',
                   coverage_limits=[
                       'Open and closed/merged PR title/body snapshots are separate and not atomic; at most40 pages of100 each, with explicit completeness.',
                       'PR file paths, patches, inline review comments and nested implementation code are not searched.',
                       'Recent discussions: latest100 bodies. Required hubs1163/1166/1167: body plus last100 comments and first20 replies per retained comment; pagination flags retained.',
                       'Closed/open duplicates use the newer updated_at record. A text-search miss is not a novelty or nonoverlap certificate.',
                       'A pending PR kappa is an author claim until separately checked; the selected reviewed record remains authoritative for selected status.'])

    def save(name, raw, source):
        data = gzip.compress(raw,mtime=0) if name.endswith('.gz') else raw
        with (output/name).open('xb') as handle:
            handle.write(data)
        receipt['files'][name] = dict(bytes=len(data),sha256=digest(data),
                                     uncompressed_sha256=digest(raw),source=source)

    def gh(args, payload=None):
        if time.monotonic()-start >= TOTAL_SECONDS:
            raise TimeoutError('bounded checkpoint wall-time budget exhausted')
        result = subprocess.run(['gh','api',*args],cwd=ROOT,
                                input=json.dumps(payload) if payload is not None else None,
                                text=True,capture_output=True,timeout=HTTP_TIMEOUT)
        if result.returncode:
            # Do not expose environment, tokens, auth configuration or raw headers.
            raise RuntimeError('read-only GitHub API request failed with exit '+str(result.returncode))
        value = json.loads(result.stdout)
        if isinstance(value,dict) and value.get('errors'):
            raise RuntimeError('GitHub GraphQL returned errors')
        return value

    for relative in GUIDANCE:
        try:
            raw = subprocess.check_output(['git','show',MAIN+':'+relative],cwd=ROOT,stderr=subprocess.DEVNULL)
            name = relative.replace('/','__')+('.txt.gz' if relative.endswith('.py') else '.gz')
            save(name,raw,dict(kind='git',commit=MAIN,path=relative))
            receipt['guidance'].append(dict(path=relative,sha256=digest(raw),
                git_blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),file=name))
            if relative.endswith('agent-task-catalog.json'):
                receipt['priority_revision'] = json.loads(raw).get('priority_revision')
            if relative.endswith('selected-result.json'):
                selected = json.loads(raw)
                receipt['selected_result'] = {k:selected.get(k) for k in ('status','kappa','decimal','review','source_manifest','reproduce','scope')}
        except subprocess.CalledProcessError:
            receipt['errors'].append(dict(kind='guidance',path=relative,error='path absent at exact pinned commit'))

    corpus = {}
    for state in ('open','closed'):
        rows, complete, pages, error = [], False, 0, None
        began = utc()
        try:
            for page in range(1,MAX_PAGES+1):
                data = gh([f'repos/{REPOSITORY}/pulls?state={state}&sort=updated&direction=desc&per_page=100&page={page}'])
                if not isinstance(data,list):
                    raise ValueError('expected PR page list')
                pages += 1
                for p in data:
                    rows.append({k:p.get(k) for k in ('number','title','body','html_url','updated_at','created_at','closed_at','merged_at','draft','state')}
                                | dict(head=p['head']['sha'],author=p['user']['login']))
                print(json.dumps(dict(phase='pulls',state=state,page=page,rows=len(rows))),flush=True)
                if len(data)<100:
                    complete = True
                    break
        except (subprocess.SubprocessError,ValueError,RuntimeError,KeyError,TimeoutError) as exc:
            error = type(exc).__name__+': '+str(exc)[:300]
        name = state+'-prs.json.gz'
        save(name,encoded(rows),dict(kind='REST',endpoint='repos/'+REPOSITORY+'/pulls',state=state,per_page=100))
        receipt['remote'][state+'_prs'] = dict(file=name,count=len(rows),pages=pages,complete=complete,
                                              started_utc=began,finished_utc=utc(),error=error)
        for row in rows:
            old = corpus.get(row['number'])
            if old is None or row['updated_at'] > old['updated_at']:
                corpus[row['number']] = row

    query = '''query { repository(owner:"CrocSwap",name:"integer-mult-bounds") {
      discussions(first:100,orderBy:{field:UPDATED_AT,direction:DESC}) {
        pageInfo {hasNextPage endCursor} nodes {number title body url updatedAt author {login}}
      }
    }}'''
    try:
        value = gh(['graphql','--input','-'],{'query':query})
        save('recent-discussions.json.gz',encoded(value),dict(kind='GraphQL',query=query))
        conn = value['data']['repository']['discussions']
        receipt['remote']['recent_discussions'] = dict(count=len(conn['nodes']),pageInfo=conn['pageInfo'])
    except (subprocess.SubprocessError,ValueError,RuntimeError,KeyError,TimeoutError) as exc:
        receipt['errors'].append(dict(kind='recent_discussions',error=type(exc).__name__+': '+str(exc)[:300]))

    for number in (1163,1166,1167):
        query = '''query { repository(owner:"CrocSwap",name:"integer-mult-bounds") {
          discussion(number:%d) {number title body url updatedAt author {login}
            comments(last:100) {pageInfo {hasPreviousPage startCursor}
              nodes {id body createdAt updatedAt author {login}
                replies(first:20) {pageInfo {hasNextPage endCursor}
                  nodes {id body createdAt updatedAt author {login}}}
              }
            }
          }
        }}'''%number
        try:
            value = gh(['graphql','--input','-'],{'query':query})
            save('discussion-'+str(number)+'.json.gz',encoded(value),dict(kind='GraphQL',query=query))
            discussion = value['data']['repository']['discussion']
            comments = discussion['comments']
            receipt['remote']['discussion_'+str(number)] = dict(comments=len(comments['nodes']),
                commentPageInfo=comments['pageInfo'],truncated_reply_threads=sum(
                    c['replies']['pageInfo']['hasNextPage'] for c in comments['nodes']),updatedAt=discussion['updatedAt'])
        except (subprocess.SubprocessError,ValueError,RuntimeError,KeyError,TimeoutError) as exc:
            receipt['errors'].append(dict(kind='discussion',number=number,error=type(exc).__name__+': '+str(exc)[:300]))

    matches = []
    for number,row in sorted(corpus.items()):
        text = row['title']+'\n'+(row['body'] or '')
        terms = [term for term in TERMS if term.lower() in text.lower()]
        if terms:
            matches.append({k:row[k] for k in ('number','title','head','author','html_url','state','updated_at')}
                           | dict(terms=terms,decimal_tokens=sorted(set(re.findall(r'0\.001[0-9]{6,}',text)))))
    save('overlap-index.json.gz',encoded(matches),dict(kind='local-text-index',terms=TERMS))
    receipt['overlap_matches'] = len(matches)
    receipt['distinct_prs'] = len(corpus)
    receipt['finished_utc'] = utc()
    receipt['elapsed_seconds'] = time.monotonic()-start
    raw = (json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode()
    with (output/'RECEIPT.json').open('xb') as handle:
        handle.write(raw)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('files','guidance')},sort_keys=True),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUT)
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(PKG/'data/continuation-02'):
        parser.error('checkpoint output must remain inside new data/continuation-02')
    main(args.output)
