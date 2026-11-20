#!/bin/bash
# Runs the hostile-disposable suite against ../qubes-dispvm-fetch without Qubes:
# tests/bin/qvm-run stands in for the real one and, with EVIL=<case>, plays a
# malicious disposable that streams a crafted archive (see evil.py).
# Needs: python3, bash, coreutils, findutils. Takes about a minute.
set -u
here=$(cd "$(dirname "$0")" && pwd)
export PATH="$here/bin:$PATH" EVILPY="$here/evil.py"
exec "$here/hostile.sh" "$here/../qubes-dispvm-fetch"
