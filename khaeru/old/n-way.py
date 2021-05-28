#!/usr/bin/env python
# coding=utf-8
"""N-way synchronization using Bazaar.

Conducts a star-topology synchronization between multiple computers and a
repository using Bazaar.

The algorithm assumes:
- a file in the same directory named '.n-way' contains configuration information
  in the format:

    [bzr]
    master = bzr+ssh://user1@example2.com:1234/home/user1/bzr-repo
    hosts = bzr+ssh://user2@example2.com:2345/home/user2/data-dir
      bzr+ssh://user3@example3.com:3456/home/user3/data-dir
      bzr+ssh://user4@example4.com:4567/home/user4/data-dir
      …

- each line of 'hosts' is a Bazaar URL for a branch that is bound to the
  repository (the 'master' URL), using 'bzr bind'.
- no host has any uncommitted changes.
- n-way.py is invoked from within one of the branches.

In this configuration, a commit on any branch will push the new revision to the
repository. In other words, the algorithm assumes none of the branches is newer
than the master.

Currently the script only checks whether each branch is out of date, and
optionally updates it.

"""
from __future__ import print_function
from ConfigParser import ConfigParser
from os import remove
from uuid import uuid1

from bzrlib.branch import Branch
from bzrlib.errors import TransportError


class StateError(StandardError):
    pass


def cmp_branch(a, b):
    """Compare branches *a* and *b*."""
    revno_a = a.revno()
    id_a = a.get_rev_id(revno_a)
    revno_b = b.revno()
    id_b = b.get_rev_id(revno_b)
    if revno_a == revno_b:
        if id_a == id_b:
            return 0
        else:
            raise StateError('%s and %s have matching revno %d but different '
              + 'revision ids (%s and %s).' % (a, b, revno_a, id_a, id_b))
    elif revno_a < revno_b:
        return -1
    else:
        return 1


# load configuration
c = ConfigParser()
c.read('.n-way')
# create branches for the master and local nodes
try:
    master = Branch.open(c.get('bzr', 'master'))
except TransportError:
    print('Error: could not connect to %s' % master.user_url)
    import sys
    sys.exit(1)
nodes = {'local': Branch.open('.'),}
# create a temporary file to identify which of the remote hosts refers to the
#   current directory
fname = ".n-way-%s" % uuid1()
open(fname, 'wa').close()
# create branches for each remote host
n = 0
for url in c.get('bzr', 'hosts').split('\n'):
    try:
        b = Branch.open(url)
    except TransportError:
        # can't connect to this host; give up silently
        pass
    else:
        # add the branch *only* if the host is not the local node
        if not b.user_transport.has(fname):
            nodes[n] = b
            n += 1
# remove the temporary file
remove(fname)
# if the master is newer than any node, update it
for k in nodes:
    if cmp_branch(nodes[k], master) == -1:
        print('Node %s is out of date. Updating…' % k)
        nodes[k].update()
    elif k == 'local':
        # confirm that the local node is up to date
        print('Local branch is up-to-date.')
