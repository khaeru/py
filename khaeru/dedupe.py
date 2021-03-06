#!/usr/bin/env python3
"""Interactively process files reported by duff, fdupes, or rdfind.

Use one of the following:
$ duff -ar . >duplicates.duff
$ fdupes -HrS . >duplicate.fdupes
$ rdfind -ignoreempty false -checksum sha1 -outputname duplicates.rdfind

(You can also prepend "/usr/bin/time -o timer" to keep track of the execution
time.)

Then call:
$ dedupe duplicates.EXT

"""
from collections import defaultdict
import os.path
from os.path import commonpath, split
import pickle
import re

import click
import tqdm

# Regex for parsing the header lines of duplicate file groups
group_re = {
    "duff": re.compile(
        r"(?P<count>\d+) files in cluster (?P<id>\d+) "
        r"\((?P<size>\d+) bytes, digest (?P<digest>\w{40})\)"
    ),
    "fdupes": re.compile(r"(?P<size>\d+) byte[s]? each:"),
}


class Group:
    next_id = 1

    def __init__(self, format, line):
        try:
            groupdict = group_re[format].match(line).groupdict()
        except AttributeError:
            raise ValueError("Unable to parse line: '%s'", line)

        self.format = format

        self.digest = groupdict.pop("digest", "")
        for k, v in groupdict.items():
            setattr(self, k, int(v))

        self.expecting = getattr(self, "count", 0)
        self.id = getattr(self, "id", Group.next_id)
        Group.next_id += 1

        self.finished = False
        self.paths = []

    def add_file(self, path):
        if self.format == "fdupes" and path.strip() == "":
            self.finished = True
            self.count = -self.expecting
            return

        self.paths.append(path)
        self.expecting -= 1

        if self.format == "duff":
            self.finished = self.expecting == 0

    def __str__(self):
        info = [
            "#{0.id:5d} — {0.count} files — {0.size} bytes — {0.digest}".format(self)
        ]

        if self.count > 10:
            paths = self.paths[:5] + ["…"] + self.paths[-5:]
        else:
            paths = self.paths

        return "\n".join(info + paths)


def determine_format(filename):
    with open(filename) as f:
        first_line = f.readline()

    for fmt, expr in group_re.items():
        if expr.match(first_line):
            return fmt

    raise ValueError("Can't determine format for initial line:\n%s", first_line)


def commonsuffix(strings):
    def gen(strs):
        N = len(strs)
        for k in zip(*map(reversed, strs)):
            if any([k[i] != k[0] for i in range(1, N)]):
                break
            yield k[0]

    return ("".join(gen(strings)))[::-1]


def read_groups(filename, format):
    groups = dict()
    index = {
        k: defaultdict(set)
        for k in ("count", "size", "cpath", "rcpath", "base", "name")
    }

    group = None
    with open(filename) as f:
        for line in tqdm.tqdm(f):
            if group:
                group.add_file(line[:-1])
            else:
                group = Group(format, line)
                groups[group.id] = group
                continue

            if group.finished:
                index["count"][group.count].add(group.id)
                index["size"][group.size].add(group.id)

                cpath = commonpath(group.paths)
                index["cpath"][cpath].add(group.id)

                rcpath = commonsuffix(group.paths)
                if "/" in rcpath:
                    index["rcpath"][rcpath].add(group.id)

                heads, tails = map(set, zip(*map(split, group.paths)))

                if len(heads) <= 2:
                    index["base"][":".join(sorted(heads))].add(group.id)

                if len(tails) <= 2:
                    index["name"][":".join(sorted(tails))].add(group.id)

                group = None

    print("Read %d groups" % len(groups))

    with open("{}.dedupe-cache".format(filename), "wb") as f:
        pickle.dump(groups, f)
        pickle.dump(index, f)

    return groups, index


@click.command()
@click.argument("filename", type=click.Path(exists=True))
@click.option("--limit", type=int, default=5)
@click.option("--use-cache", is_flag=True)
def cli(filename, limit, use_cache):
    if use_cache:
        with open("{}.dedupe-cache".format(filename), "rb") as f:
            groups = pickle.load(f)
            index = pickle.load(f)
    else:
        fmt = determine_format(filename)
        groups, index = read_groups(filename, fmt)

    for by, idx in index.items():
        print("%d clusters by %s" % (len(idx), by))

        count = limit
        for k, v in reversed(sorted(idx.items())):
            print("%s '%s': %d group(s) with ids %s" % (by, k, len(v), v))

            for group_id in v:
                print(groups[group_id])

            print("")

            count -= 1
            if count == 0:
                break


# Old methods


def file_recursive(target, path, data):
    key = path.pop(0)
    if key not in target:
        target[key] = dict()
    if len(path):
        file_recursive(target[key], path, data)
    else:
        target[key][data["id"]] = data


def print_group(g, indent=0):
    """Print information about a group of duplicate files."""
    indent_ = "  " * indent


def ls(path):
    """List groups and subdirectories at *path*."""
    target = groups_by_path
    for dir in path.split("/"):
        target = target[dir]
    for k, v in target.items():
        if type(k) is int:
            print_group(v)
        else:
            print("{} {}".format(len(v), k))


def prune(id_):
    cpath = os.path.commonpath(groups_by_id[id_]["files"]).split("/")
    target = [groups_by_path]
    for dir in cpath:
        target.append(target[-1][dir])
    # Prune the selected group
    del target[-1][id_]
    # Prune empty directories
    for i in reversed(range(1, len(target))):
        if len(target[i]) == 0:
            del target[i - 1][cpath[i - 1]]


def skip(id_):
    if id_ not in done["skip"]:
        done["skip"].add(id_)
        prune(id_)
