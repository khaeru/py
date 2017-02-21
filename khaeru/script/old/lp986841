#!/usr/bin/env python3
# https://bugs.launchpad.net/ubuntu/+source/acroread/+bug/986841/comments/21

import mmap, sys

target = br'C:\nppdf32Log\debuglog.txt'
replacement = br'/dev/null'
replacement += b'\0' * (len(target) - len(replacement))

with open(sys.argv[1], 'r+') as f:
  m = mmap.mmap(f.fileno(), 0)
  offset = m.find(target)
  assert offset != -1
  m[offset:offset+len(target)] = replacement
