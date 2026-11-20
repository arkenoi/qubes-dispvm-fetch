import io, sys, tarfile, time
case = sys.argv[1]
out = sys.stdout.buffer
t = tarfile.open(fileobj=out, mode="w|", format=tarfile.PAX_FORMAT)
def f(name, data=b"x", **kw):
    ti = tarfile.TarInfo(name); ti.size = len(data)
    for k, v in kw.items(): setattr(ti, k, v)
    t.addfile(ti, io.BytesIO(data))
def special(name, typ, **kw):
    ti = tarfile.TarInfo(name); ti.type = typ
    for k, v in kw.items(): setattr(ti, k, v)
    t.addfile(ti)
f("ok/readme.txt", b"hello")
if case == "traversal": f("../escaped.txt")
elif case == "abs": f("/tmp/abs-escape.txt")
elif case == "dotdot-mid": f("ok/../../escaped2.txt")
elif case == "symlink-then-write":
    special("ok/link", tarfile.SYMTYPE, linkname="/tmp"); f("ok/link/pwned.txt")
elif case == "hardlink": special("ok/hard", tarfile.LNKTYPE, linkname="/etc/passwd")
elif case == "device": special("ok/dev", tarfile.CHRTYPE, devmajor=1, devminor=3)
elif case == "fifo": special("ok/fifo", tarfile.FIFOTYPE)
elif case == "escape-name": f("ok/\x1b]0;owned\x07\x1b[31mred.txt")
elif case == "bidi": f("ok/invoice‮txt.exe")
elif case == "dup": f("ok/readme.txt", b"second")
elif case == "file-then-dir": f("ok/a"); f("ok/a/b")
elif case == "setuid-exec": f("ok/run.sh", b"#!/bin/sh\n", mode=0o4777)
elif case == "toobig": f("ok/big.bin", b"A" * 3_000_000)
elif case == "manyfiles":
    for i in range(50): f(f"ok/f{i}")
elif case == "pax-path": f("innocent.txt", pax_headers={"path": "../pax-escape.txt"})
elif case == "trailing-garbage":
    t.close(); out.write(b"Z" * 50_000_000); sys.exit(0)
elif case == "stderr-escape":
    sys.stderr.write("\x1b]0;pwned-title\x07\x1b[2J evil stderr\n")
elif case == "hang":
    t.close(); out.flush(); time.sleep(60); sys.exit(0)
elif case == "fail": t.close(); sys.exit(3)
elif case == "git-config":
    f("ok/.git/config", b"[core]\n\tfsmonitor = touch /tmp/pwned-fsmonitor\n")
    f("ok/sub/.GIT/hooks/post-checkout", b"#!/bin/sh\ntouch /tmp/pwned\n")
elif case == "many-dirs":
    for i in range(50):
        ti = tarfile.TarInfo(f"ok/d{i}"); ti.type = tarfile.DIRTYPE; t.addfile(ti)
elif case == "pax-huge":
    # raw pax extended header claiming ~1.5 GB, then actually send it
    import tarfile as tf
    # leave the tar stream open; write raw blocks
    hdr = tf.TarInfo("PaxHeaders/x"); hdr.type = tf.XHDTYPE; hdr.size = 1_500_000_000
    out.write(hdr.tobuf(format=tf.USTAR_FORMAT))
    blk = b"9" * (1024 * 1024)
    for _ in range(1500): out.write(blk)
    sys.exit(0)
elif case == "stderr-flood":
    sys.stderr.write("E" * 100_000_000); sys.stderr.flush()
t.close()
