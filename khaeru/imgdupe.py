"""Usage: imgdupe DIR1 DIR2

Find image files in DIR1 and DIR2 with matching names and image data, but
possibly different sizes or (EXIF etc.) metadata. ImageMagick ('identify'
binary, which must be available) is used to compute the SHA-256 of the image
*data* only.

The list of duplicate files is written to duplicates.txt.

Tips!
- The verbose output can be captured by piping to 'tee'.
- Use something like "cat duplicates.txt | tr '\n' '\0' | xargs -0 gvfs-trash"
  to reversibly delete the duplicate files.

"""

from collections import defaultdict
from itertools import combinations
import os
import os.path
import re
from subprocess import check_output
import sys

# Locate all images in the named directories
fnre = re.compile("^.*jpg$", flags=re.IGNORECASE)
images = set()
for i, path in enumerate(sys.argv[1:]):
    for dirpath, dirnames, filenames in os.walk(path):
        images |= {(fn, i, dirpath) for fn in filenames if fnre.match(fn) is not None}

# The priority (i) in the tuple should cause higher-priority files with the
# same name to sort first
images = sorted(images)

# Identify filenames which appear more than once; save the other data for these
dupes = defaultdict(set)
for i in range(1, len(images)):
    if images[i - 1][0] == images[i][0]:
        dupes[images[i][0]] |= {images[i - 1][1:], images[i][1:]}

# Full paths of files which are duplicates, but NOT originals
duplicates = []
of = open("duplicates.txt", "w")

fail = False  # Flag for a condition we can't handle
for bn, dirs in dupes.items():  # Iterate over duplicated filenames
    details = dict()
    for dir in dirs:  # Iterate over instances of the filename *bn*
        fn = os.path.join(dir[1], bn)
        # ImageMagick hash and EXIF data
        cmd = ["identify", "-quiet", "-format", "%#\n%[exif:*]", fn]
        hash, _, exif = check_output(cmd).decode().partition("\n")
        # Other file information. Inode number is not currently used, but could
        # be used to check for hardlinks to the same inode.
        stat = os.stat(fn, follow_symlinks=False)
        details[fn] = (dir[0], hash, exif, int(stat.st_mtime), stat.st_ino)
    # Pairwise compare duplicates. In a group of >2 duplicates, the highest-
    # priority fill will 'win' all the comparisons it appears in, and will not
    # be added to *duplicates*
    for f1, f2 in combinations(details.items(), 2):
        skip = False
        if f1[1][1] == f2[1][1]:  # Compare hashes
            if f1[1][0] > f2[1][0]:  # Compare priorities
                f1, f2 = f2, f1  # Swap so that *f1* is higher priority
                if f1[1][3] < f2[1][3]:
                    fail = "File with greater priority has older mtime."
            elif f1[1][0] == f2[1][0]:
                skip = (
                    "Files have matching priority, unable to determine "
                    "which is the duplicate; skipping."
                )
            # commented: don't care about this for the moment
            # # Compute a diff between the EXIF data of the two images
            # diff = unified_diff(f1[1][2].split('\n'), f2[1][2].split('\n'),
            #                    lineterm='')
            # Display verbose output
            print(
                (
                    "Matching hash: {0[1][1]}\n"
                    "\t{0[1][0]} {0[1][3]} {0[0]}\n"
                    "\t{1[1][0]} {1[1][3]} {1[0]}\n"
                    "{2}"
                ).format(
                    f1,
                    f2,
                    ""
                    # commented: output the EXIF diff
                    # '\n'.join(diff)
                ),
                flush=True,
            )
            assert not fail, fail  # Some condition we don't know how to handle
            if skip:  # Don't do anything about this comparison
                print(skip)
                continue
            else:  # Add f2 to the list of duplicates
                duplicates.append(f2[0])
                of.write(f2[0] + "\n")
        else:  # Hashes don't match
            print(
                "Matching filenames, distinct hash:\n\t{}\n\t{}\n".format(f1[0], f2[0]),
                flush=True,
            )
