"""Tool for choosing duplicate files to save from a Maildir mailbox

OfflineIMAP, if used badly (as I do) can create duplicates of many messges.
Used with the tool fdupes, this script can produce a list of messages that
can be deleted.

Usage:
  fdupes -r1n .local/share/offlineimap/Maildir/INBOX | egrep -v "(cmeta|ibex)"\
    >dupes.txt
  python dupes.py >remove.txt
  cat remove.txt | xargs rm

Piping directly to 'xargs rm' is probably dumb. The program throws an exception
if it fails to save exactly one file from a set of duplicates.

"""
from os.path import basename, commonprefix, dirname, reduce
import sys


lines = open(sys.argv[1]).readlines()
prefix = dirname(commonprefix(lines))
sets = [L.rstrip().replace(" %s" % prefix, "\t%s" % prefix).split("\t") for L in lines]

for s in sets:
    s = sorted(s)

    #   matches in different folders
    root = dirname(commonprefix(s))
    if root == "./Maildir/INBOX":
        print(s)
        continue

    # temporary files or those with incomplete names
    for i in range(len(s)):
        try:
            if s[i].endswith("khaeru-laptop") or "/tmp/" in s[i]:
                print(s.pop(i))
                i -= 1
        except IndexError:
            pass

    # descisions based on message flags
    flags = [basename(f).split(",")[-1] for f in s]

    if reduce(lambda a, b: a and b, map(lambda s: s == flags[0], flags)):
        # all flags the same, delete all but one file
        while len(s) > 1:
            print(s.pop())
    else:
        # longest flag
        for f in flags:
            if len(f) == max(map(len, flags)):
                flag = f
                continue
        for i in range(len(s)):
            try:
                if not s[i].endswith(flag):
                    print(s.pop(i))
                    i -= 1
            except IndexError:
                pass

    # deleting too many or too few files from this set
    if len(s) != 1:
        print("BLARG!", s, "\n")
        raise SystemExit(0)
