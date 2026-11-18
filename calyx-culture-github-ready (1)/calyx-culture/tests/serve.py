#!/usr/bin/env python3
"""Tiny static server that behaves like Netlify for this site: it applies site/_headers (so the real
Content-Security-Policy is enforced in the browser tests) and the 200 rewrites in site/_redirects.
Usage: python3 tests/serve.py [port]   (default 8077)"""
import http.server, os, re, sys, socketserver
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site'))
def rx(p): return re.compile('^' + re.escape(p).replace(r'\*', '.*') + '$')
def load_headers():
    rules, cur = [], None
    for ln in open(os.path.join(ROOT, '_headers'), encoding='utf-8'):
        if not ln.strip(): continue
        if not ln.startswith((' ', '\t')): cur = (rx(ln.strip()), []); rules.append(cur)
        else: k, v = ln.strip().split(':', 1); cur[1].append((k.strip(), v.strip()))
    return rules
def load_redirects():
    out = []
    for ln in open(os.path.join(ROOT, '_redirects'), encoding='utf-8'):
        ln = ln.strip()
        if not ln or ln.startswith('#'): continue
        a, b, c = ln.split()[:3]
        if c.startswith('200'): out.append((rx(a), b))
    return out
HEAD, RED = load_headers(), load_redirects()
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(s, *a): pass
    def do_GET(s):
        s._orig = s.path.split('?')[0].split('#')[0]
        fs = os.path.join(ROOT, s._orig.lstrip('/'))
        if not (os.path.isfile(fs) or (os.path.isdir(fs) and os.path.isfile(os.path.join(fs, 'index.html')))):
            for r, to in RED:
                if r.match(s._orig): s.path = to; break
            else:
                s._nf = True
        if getattr(s, '_nf', False):
            body = open(os.path.join(ROOT, '404.html'), 'rb').read()
            s.send_response(404); s.send_header('Content-Type', 'text/html; charset=utf-8'); s.send_header('Content-Length', str(len(body))); s.end_headers(); s.wfile.write(body); return
        super().do_GET()
    def end_headers(s):
        seen = {}
        for r, hs in HEAD:
            if r.match(getattr(s, '_orig', '/')):
                for k, v in hs: seen.setdefault(k, []).append(v)
        for k, vs in seen.items(): s.send_header(k, ', '.join(vs))
        super().end_headers()
class T(socketserver.ThreadingTCPServer): allow_reuse_address = True
if __name__ == '__main__':
    T(('127.0.0.1', int(sys.argv[1]) if len(sys.argv) > 1 else 8077), H).serve_forever()
