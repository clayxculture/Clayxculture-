#!/usr/bin/env python3
"""Adds a content hash to every /assets/... reference ("?v=1a2b3c4d") so browsers cache assets for a year
and still pick up a change the moment a file changes. Run after editing anything in site/assets/:
    python3 tools/stamp.py
"""
import glob, hashlib, os, re
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
def h(p): return hashlib.sha256(open(os.path.join(R, p.lstrip('/')), 'rb').read()).hexdigest()[:8]
n = 0
for f in glob.glob(os.path.join(R, '*.html')):
    s = open(f, encoding='utf-8').read()
    t = re.sub(r'(/assets/[\w.-]+)\?v=\w+', lambda m: f'{m.group(1)}?v={h(m.group(1))}', s)
    if t != s: open(f, 'w', encoding='utf-8').write(t); n += 1
print('stamped', n, 'files')
