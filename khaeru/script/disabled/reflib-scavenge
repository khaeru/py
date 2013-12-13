#!/usr/bin/env python3
"""Usage: {} REFLIB BIBTEX

Scavenge data from a Referencer .reflib file REFLIB, insert into a .bib file
BIBTEX

Referencer stores bibliography data in an XML format, and optionally maintains
a file in BibTeX format. Some XML tags, such as <filename> and
<relative_filename>, are not exported to this BibTeX file.

This script transfers the contents of <relative_filename> tags to the BibTeX
file key 'localfile' for the corresponding entries.
"""
from collections import OrderedDict
from os.path import exists
import re
import sys
from urllib.parse import unquote

from bs4 import BeautifulSoup


def read_bib(f):
    """Read BibTeX entries from file *f*.

    Assumes entries are separated by blank lines, and there are no blank lines
    within entries. Returns a collections.OrderedDict, in which all BibTeX
    entries are stored as strings under their BibTeX keys, and other non-entry
    content of *f* is preserved in order.
    """
    entries = OrderedDict()
    prog = re.compile("@[^{]*{([^,]*),\n")
    # state:
    # - None: the next line is start of a new entry, or non-entry BibTeX code
    #   like a @comment
    # - any other value: either the key of an entry, or the first line of non-
    #   entry code in a non-entry block
    current = None
    for line in f:  # process the file linewise
        if current is None:  # next line might be the start of a new entry
            key = prog.match(line)
            if key:  # it is
                current = key.groups()[0]
            else:  # it's some non-entry code
                current = line
            entries[current] = line  # store the line itself
        elif line == '\n':  # a blank line; we're between entries or other code
            current = None
        else:  # currently reading an entry, append to it
            entries[current] += line
    return entries


if __name__ == '__main__':
    # input
    try:
        # read and parse the Referencer XML file
        soup = BeautifulSoup(open(sys.argv[1], 'r'), 'xml')
        # read and parse the BibTeX file
        with open(sys.argv[2], 'r') as f:
            bib = read_bib(f)
    except IndexError:
        print(__doc__.format(sys.argv[0]))
        sys.exit(1)
    # transfer the filenames
    for t in soup.find_all('doc'):
        if t.relative_filename.text == '':
            continue
        key = t.key.text
        fn = unquote(t.relative_filename.text)
        if not exists(fn):
            print('Found "{}" for {}, but file is missing.'.format(fn, key))
        elif key not in bib:
            print('Found "{}" for {}, but no matching entry in {}.'.format(fn,
                  key, sys.argv[2]))
        else:
            bib[key] = bib[key].replace('\n\t', ('\n\tlocalfile = {{{}}},\n\t'
                                                 ).format(fn), 1)
            continue
        sys.exit(1)
    # output
    with open('{}.scavenged'.format(sys.argv[2]), 'w') as f:
        # re-add blank lines between entries, and a terminal blank line
        f.write('\n'.join(bib.values()) + '\n')
