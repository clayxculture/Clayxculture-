#!/usr/bin/env bash
# Runs the browser tests against the site folder with a mocked backend.
# One-time setup:  pip install playwright && playwright install chromium
cd "$(dirname "$0")"; mkdir -p out
python3 serve.py 8077 >/dev/null 2>&1 &
SRV=$!; trap "kill $SRV" EXIT; sleep 1
for t in e2e.py e2e_new.py e2e_rev.py e2e_admin.py e2e_empty.py e2e_pages.py e2e_shop.py e2e_standalone.py e2e_delivery.py; do echo "== $t"; python3 $t 2>&1 | grep -v "Failed to load" | tail -6; done
