"""SIGALRM deadline for the main thread (the vendored PR1186 rev1 toolkit predates compat.py)."""
import contextlib, signal
class Timeout(Exception): pass
@contextlib.contextmanager
def deadline(seconds):
    def on_alarm(sig, frame): raise Timeout()
    old = signal.signal(signal.SIGALRM, on_alarm); signal.setitimer(signal.ITIMER_REAL, seconds)
    try: yield
    finally: signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, old)
