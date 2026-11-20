#!/bin/bash
# usage: hostile.sh SCRIPT  (run with fake qvm-run on PATH)
S=$1; T=$(cd "$(dirname "$0")" && pwd); D=$T/hdest
pass=0; fail=0
check() {  # case expected-exit extra-args...
  local c=$1 want=$2; shift 2
  rm -rf "$D" /tmp/abs-escape.txt "$T"/escaped*.txt "$T"/pax-escape.txt; mkdir -p "$D"
  out=$(cd "$D" && EVIL=$c timeout 120 "$S" --dest "$D" "$@" https://example.org/x.tar 2>&1); rc=$?
  problems=""
  [ "$want" = 0 ] && [ $rc -ne 0 ] && problems+=" expected-success(rc=$rc)"
  [ "$want" = 1 ] && [ $rc -eq 0 ] && problems+=" expected-rejection"
  ls -d "$D"/.incoming-* >/dev/null 2>&1 && problems+=" staging-left-behind"
  for f in /tmp/abs-escape.txt "$T"/escaped.txt "$T"/escaped2.txt "$T"/pax-escape.txt "$D"/../escaped.txt; do [ -e "$f" ] && problems+=" ESCAPED:$f"; done
  [ -n "$(find "$D" -type l)" ] && problems+=" symlink-created"
  [ -n "$(find "$D" -type f -perm /7111)" ] && problems+=" exec-or-suid-bits"
  [ -n "$(find "$D" ! -type f ! -type d)" ] && problems+=" special-file"
  printf '%s' "$out" | grep -q $'\x1b' && problems+=" RAW-ESCAPE-IN-OUTPUT"
  if [ -z "$problems" ]; then pass=$((pass+1)); st=OK; else fail=$((fail+1)); st="FAIL:$problems"; fi
  printf '%-20s rc=%-3s %-6s | %s\n' "$c" "$rc" "$st" "$(printf '%s' "$out" | grep -E 'REJECTED|received|skipped' | head -2 | tr '\n' ' ' | cut -c1-110)"
}
check traversal 1
check abs 1
check dotdot-mid 1
check pax-path 1
check symlink-then-write 0
check hardlink 0
check device 1
check fifo 1
check escape-name 1
check bidi 1
check dup 1
check file-then-dir 1
check setuid-exec 0
check toobig 1 --max-bytes 1000000
check manyfiles 1 --max-files 10
check trailing-garbage 1 --max-bytes 1000000
check fail 1
check hang 1 --timeout 5
check stderr-escape 0
check stderr-flood 0
check pax-huge 1
echo "passed=$pass failed=$fail"
