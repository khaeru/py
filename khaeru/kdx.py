"""USAGE: {} MOUNT [MAP]
Add documents on the Kindle DX mounted at MOUNT to collections according to
MAP. MAP should be a JSON document in the format:

  { DIR1: C1

http://kcollect.googlecode.com/svn/trunk/kcollect

"""
from collections import defaultdict
from hashlib import sha1
import json
import os
import os.path
import sys


HASH_PREFIX = "/mnt/us/"
LANG = "en-US"
FILEEXT = [
    "pdf",
]


def compute_hash(fn):
    """Compute the Kindle DX hash for file name *fn*

    *fn* should be given relative to the mount root
    """
    return sha1((os.path.join(HASH_PREFIX, fn)).encode()).hexdigest()


# commented: currently unused
# def touch_collection(data, cname):
#    """Create a collection *cname* in collection list *data*."""
#    cname = 'name@{}'.format(LANG)
#    if cname not in data.keys():
#        ts = int(datetime.now(timezone.utc).timestamp() * 1000)
#        data[cname] = dict(items=list(), lastAccess=ts)


def add_file(data, collection, filepath):
    """Add *filepath* to collection *cname* in collection list *data*"""
    fhash = "*{}".format(compute_hash(filepath))
    if fhash not in kdx[current]["items"]:
        kdx[current]["items"].append(fhash)
        return True
    else:
        return False


try:
    mnt_root = os.path.join(sys.argv[1], "documents")
    with open(os.path.join(sys.argv[1], "system", "collections.json")) as f:
        kdx = json.load(f)
    if len(sys.argv) == 3:
        fn = sys.argv[2]
    elif len(sys.argv) == 2:
        fn = os.path.join(sys.argv[1], "system", "map.json")
    else:
        raise IndexError
    with open(fn) as f:
        map = json.load(f)
except IndexError:
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)
except FileNotFoundError as e:
    raise e

found = defaultdict(list)
added = defaultdict(list)

for root, dirs, files in os.walk(os.path.join(sys.argv[1], "documents"), topdown=False):
    root = root.split(sys.argv[1])[1].lstrip(os.path.sep)
    if root in map:  # this directory explicitly assigned to a collection
        current_base = root
    elif any([d in root for d in map.keys()]):
        current_base = list(filter(lambda d: d in root, map.keys()))[0]
    else:
        continue
    current = "{}@{}".format(map[current_base], LANG)
    print("{} matches collection {}".format(root, current))
    for f in files:
        if os.path.splitext(f)[1][1:] not in FILEEXT:
            continue
        if add_file(kdx, current, os.path.join(root, f)):
            added[current_base].append(f)
        else:
            found[current_base].append(f)

for root, name in map.items():
    a = set(kdx["{}@{}".format(name, LANG)]["items"])
    b = set(found[root])
    c = set(added[root])
    print("{}:\n  {} listed, {} found, {} added".format(name, len(a), len(b), len(c)))

with open(os.path.join(sys.argv[1], "system", "collections.json.new"), "w") as f:
    json.dump(kdx, f, separators=(",\n", ":\n"))
