"""deadline/Timeout/peak_rss_gib from our #1186 rev3 toolkit's compat.py (copied: #1957's vendored toolkit predates it)."""
import importlib.util, os
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'toolkit', 'compat.py')
_s = importlib.util.spec_from_file_location('eft_compat', _p); _m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
deadline, Timeout, peak_rss_gib = _m.deadline, _m.Timeout, _m.peak_rss_gib
