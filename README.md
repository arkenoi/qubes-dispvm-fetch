# qubes-dispvm-fetch

Fetch a file or a git repository **in a disposable qube** and bring it into
**dom0** under `~/QubesIncoming/dispvm-fetch/`, without letting the disposable
write anything else in dom0.

One self-contained Python 3 file, no dependencies beyond what Qubes dom0 ships.

```
qubes-dispvm-fetch https://example.org/release.tar.gz --sha256 <hex>
qubes-dispvm-fetch https://github.com/QubesOS/qubes-core-admin-client.git
qubes-dispvm-fetch --git --ref v4.3.0 https://github.com/QubesOS/qubes-core-admin-client
```

On success it prints the path of the new directory, e.g.
`~/QubesIncoming/dispvm-fetch/20261120-194438-qubes-core-admin-client/`.

## Install (dom0)

dom0 has no network, so fetch the script in a qube, read it, then copy it in:

```
# in dom0
mkdir -p ~/bin
qvm-run --pass-io <qube> 'cat qubes-dispvm-fetch/qubes-dispvm-fetch' > ~/bin/qubes-dispvm-fetch
chmod +x ~/bin/qubes-dispvm-fetch
```

Run it as your normal dom0 user (it refuses to run as root).

## How it works

1. `qvm-run --dispvm=<template> --pass-io --no-gui` starts a fresh disposable
   (default: `qubes-prefs default_dispvm`). Inside it, `curl` or `git clone
   --depth 1` fetches the URL into a temp dir on disk, and the result is sent
   back to dom0 as a tar stream on stdout.
2. dom0 never runs `tar`, `git` or any archive tool on that stream. The script
   parses it itself and, before writing anything:
   - accepts only regular files and directories; **symlinks and hardlinks are
     skipped** (listed, never created); device files and FIFOs reject the whole
     transfer;
   - drops anything under a `.git` directory (any case), unless `--keep-git`.
     This is enforced in dom0, not left to the disposable;
   - rejects absolute paths, `..`, empty or `.` components, names with control
     or Unicode format characters (terminal escapes, bidi overrides), names that
     are not valid UTF-8, overlong names and paths deeper than 64 levels;
   - rejects duplicate entries and a path used as both file and directory;
   - enforces limits on total size (`--max-bytes`, default 2 GiB), entry count
     (`--max-files`, default 100 000: files, directories and links all count), raw stream size, data after the end of the
     archive (more than 1 MiB), and time (`--timeout`, default 30 min);
   - caps its own memory (768 MiB address space) so oversized pax/longname
     headers can't exhaust dom0 RAM.
3. Files are created fresh with `O_EXCL | O_NOFOLLOW`, mode `0644`
   (directories `0755`). **All archive metadata is ignored**: no exec bits, no
   setuid, no ownership, no timestamps.
4. Everything goes into a hidden staging directory next to the destination and
   is renamed into place only if the whole transfer passed. On any failure the
   staging directory is deleted.
5. The disposable's stderr is shown prefixed with `[dispvm]`, with control
   characters escaped and line length/count bounded, so it can't inject
   terminal escape sequences into your dom0 terminal.
6. To stop the disposable (timeout or rejection) the script sends `qvm-run`
   SIGINT first, because `qvm-run` destroys the disposable on SIGINT but not on
   SIGKILL. It escalates to SIGTERM and SIGKILL only if `qvm-run` doesn't exit.

## Options

| Option | Meaning |
|---|---|
| `--git` / `--file` | force git clone or plain download (default: git if the URL ends in `.git`) |
| `--ref REF` | git branch or tag |
| `--sha256 HEX` | expected hash of a `--file` download, verified **in dom0** |
| `--dispvm TEMPLATE` | disposable template to use |
| `--name NAME` | name for the result (sanitised to `[A-Za-z0-9._-]`) |
| `--dest DIR` | parent directory (default `~/QubesIncoming/dispvm-fetch`) |
| `--max-bytes N`, `--max-files N`, `--timeout S` | limits (`--max-files` counts every entry) |
| `--allow-http` | allow plain http (default: https only, also for redirects) |
| `--keep-git` | keep `.git` (see below) |

## Things to know

- **`.git` is dropped by default**, both in the disposable and again in dom0.
  An untrusted `.git/config` can set options such as `core.fsmonitor` or
  `core.pager` that make any later `git status`, `git log` and so on, run in
  that directory *in dom0*, execute arbitrary commands.
- **Never run git inside a received directory in dom0**, with or without
  `--keep-git`: a directory laid out like a bare repository (`HEAD`, `objects/`,
  `refs/`, `config`) is treated as one by git too. Copy files out instead.
- **Exec bits are always dropped.** Scripts you fetched won't be executable
  until you `chmod` them yourself.
- **Symlinks are not reproduced.** Repositories that rely on them will be
  incomplete; the skipped paths are listed.
- The result is still untrusted *content*. This tool keeps it contained in its
  directory; it does not make it safe to open, build or execute in dom0.

## Tests

`tests/run-tests.sh` runs 23 hostile-disposable cases without Qubes: a stand-in
`qvm-run` plays a malicious disposable that streams crafted archives (path
traversal, absolute paths, pax path override, symlink-then-write, hardlink,
device, FIFO, escape-sequence and bidi names, duplicates, file/dir clash,
setuid, oversize, too many files, trailing garbage, failure exit, hang, stderr
escape sequences, stderr flood, a 1.5 GB pax header, a planted `.git/config`
with an `fsmonitor` command, 50 directories over an entry limit of 10). For each case it checks
that nothing was written outside the destination, no staging directory is left,
no symlink, special file, `.git`, exec or setuid bit exists, and no raw escape
sequence reached the terminal.

```
tests/run-tests.sh      # passed=23 failed=0
```

**Not yet verified on a real dom0.** The disposable side was tested with
`curl`/`git` run locally; `qvm-run` behaviour (command via `qubes.VMShell`,
exit-code pass-through, cleanup on SIGINT) was checked against the
`qubes-core-admin-client` source only. After your first rejected or timed-out
run, check `qvm-ls` for a leftover `disp####` qube.

## License

MIT
