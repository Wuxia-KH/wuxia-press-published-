#!/usr/bin/env bash
# After editing assets/site.css or assets/intro.js, run this before pushing:
# it stamps index.html's and deploy.html's links with each file's content hash, so browsers
# that cached the old file (GitHub Pages sends max-age=600) fetch the new one.
set -euo pipefail
cd "$(dirname "$0")"
for page in index.html deploy.html; do
	for f in assets/site.css assets/intro.js assets/deploy.js; do
		h=$(shasum "$f" | cut -c1-8)
		sed -i.bak -E "s#(${f})(\?v=[0-9a-f]+)?\"#\1?v=${h}\"#" "$page"
	done
	rm -f "$page.bak"
done
grep -o 'assets/[a-z]*\.\(css\|js\)?v=[0-9a-f]*' index.html deploy.html
