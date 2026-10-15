"""driver.py: run build.py jobs with at most 3 concurrent processes, a per-job wall-clock timeout and a 6 GiB RSS cap.
usage: driver.py JOBS.json OUT.jsonl  (JOBS: list of argv tails for build.py)"""
import json, subprocess, sys, time, threading, os
JOBS = json.load(open(sys.argv[1])); OUT = sys.argv[2]; HERE = os.path.dirname(os.path.abspath(__file__))
CAP = 6 * 1024 ** 3; TO = 900; lock = threading.Lock(); out = open(OUT, 'a')
def rss(pid):
    try: return int(subprocess.run(['ps', '-o', 'rss=', '-p', str(pid)], capture_output=True, text=True).stdout.strip() or 0) * 1024
    except Exception: return 0
def run(job):
    t0 = time.time(); p = subprocess.Popen([sys.executable, '-B', os.path.join(HERE, 'build.py')] + job, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    status = None
    while p.poll() is None:
        if time.time() - t0 > TO: p.kill(); status = 'timeout'
        elif rss(p.pid) > CAP: p.kill(); status = 'rss-cap'
        time.sleep(1)
    text = p.stdout.read(); last = [l for l in text.splitlines() if l.startswith('{')]
    rec = json.loads(last[-1]) if last and status is None else dict(name=job[4], status=status or 'error', tail=text[-400:])
    rec['seconds'] = round(time.time() - t0, 1)
    with lock: out.write(json.dumps(rec) + '\n'); out.flush(); print(rec.get('name'), rec.get('status'), rec.get('delta'), rec.get('audit', rec.get('why', ''))[:120], flush=True)
queue = list(JOBS); threads = []
def worker():
    while True:
        with lock:
            if not queue: return
            job = queue.pop(0)
        run(job)
for _ in range(3): t = threading.Thread(target=worker); t.start(); threads.append(t)
for t in threads: t.join()
