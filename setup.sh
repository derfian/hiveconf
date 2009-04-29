#!/bin/sh

last_working=""

# Create .pth files
for binary in python2 python2.2 python2.3 python2.4 python2.5 python2.6 python _python_preferred_; do
    if ${binary} -c "" 2>/dev/null; then
        last_working=${binary}
        ${binary} - <<EOF
pthfile="hiveconf.pth"
mod_dir="/usr/lib/hiveconf"
import sys
sitedirs = filter(lambda s: s.endswith("site-packages") or s.endswith("dist-packages"), sys.path)
if len(sitedirs) < 1:
    sys.exit("Unable to find a site packages directory in sys.path")
filename = sitedirs[0] + "/" + pthfile
open(filename, "w").write(mod_dir + "\n")
print "Created", filename
EOF
    fi
done

# Modify hashbang of hivetool
if [ ${last_working} ]; then
    ${last_working} - <<EOF
import sys, os
binary = sys.executable
if binary[-len("_python_preferred_"):] == "_python_preferred_":
    binary = os.readlink(binary)
f = open("/usr/bin/hivetool", "r+")
lines = f.readlines()
lines[0] = "#!%s\n" % binary
f.seek(0)
f.writelines(lines)
f.truncate()
f.close()
EOF
fi
