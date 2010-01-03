#!/usr/bin/env python
# coding=utf8
"""Merge moinmoin data from multiple installations."""
from optparse import OptionParser
import os, os.path
import re
import shutil


def alter_page_edit_log(page_dir):
    """Update the per-page edit-log of *page* in the destination directory."""
    # read edit log
    log = []
    page_filename = os.path.join(page_dir, 'edit-log')
    if os.path.exists(page_filename):
        for line in open(page_filename, 'r').readlines():
            line = line.split('\t')
            # apply page and user maps
            for (old, new) in page_map:
                line[3] = line[3].replace(old, new)
            for (old, new) in user_map:
                line[6] = line[6].replace(old, new)
            log.append(line)
        log = sorted(log, cmp=lambda x, y: cmp(x[0], y[0]))
        # write the altered log
        if not dry_run:
            dest_file = open(page_filename, 'w')
            dest_file.writelines(['\t'.join(line) for line in log])
            dest_file.close()
        else:
            print "Writing edit log at '%s' \n\n" % page_dir
#            print ''.join(['\t'.join(line) for line in log])
#            print '\n\n'
    else:
        print "Page at '%s' has no edit log, skipping.\n\n" % page_dir


def build_page_list(args):
    # default: all pages
    if args == []:
        args.append('.*')
    # list all pages in source directory and filter
    exp = re.compile('|'.join(args))
    p1 = filter(lambda p: exp.match(p), os.listdir(os.path.join(source_dir,
      'pages')))
    # apply page name mapping
    p2 = p1
    for (old, new) in page_map:
        p2 = map(lambda p: p.replace(old, new), p2)
    pages = zip(p1, p2)
    # check for page name collisions
    for i in range(len(pages)):
        if os.path.exists(os.path.join(dest_dir, pages[i][1])):
            print "Destination page '%s' exists, skipping." % pages[i][1]
            del pages[i]
            i -= 1
    print '\n'.join(['\t'.join(p) for p in pages])
    return pages


def copy_data(pages):
    # copy pages and alter logs
    for (old_page, new_page) in pages:
        src = os.path.join(source_dir, 'pages', old_page)
        dst = os.path.join(dest_dir, 'pages', new_page)
        # copy the directory
        if not dry_run:
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('cache'))
            # clean up the page log
            alter_page_edit_log(dst)
        else:
            print 'copy_data: %s → %s' % (src, dst)
            alter_page_edit_log(src)
    # copy users
    (old_users, junk) = zip(*user_map)
    users = os.listdir(os.path.join(source_dir, 'user'))
    i = 0
    while i < len(users):
        if users[i] in old_users:
            print "copy_data: Skipping old user '%s'." % users[i]
            del users[i]
        else:
            i += 1
    print "copy_data: %d users to copy." % len(users)
    for user in users:
        src = os.path.join(source_dir, 'user', user)
        dst = os.path.join(dest_dir, 'user', user)
        if os.path.exists(dst):
            print "copy_data: Destination user '%s' exists, skipping." % user
        else:
            if not dry_run:
                shutil.copy2(src, dst)
            else:
                print 'copy_data: %s → %s' % (src, dst)


def merge_logs(pages):
    """Merge the edit-log and event-log files."""
    (source_pages, dest_pages) = zip(*pages)
    # read source edit log
    log = []
    total_lines = 0
    for line in open(os.path.join(source_dir, 'edit-log'), 'r').readlines():
        line = line.split('\t')
        # old merge lines related to pages being moved
        if line[3] in source_pages:
            # apply page and user maps
            for (old, new) in page_map:
                line[3] = line[3].replace(old, new)
            for (old, new) in user_map:
                line[6] = line[6].replace(old, new)
            log.append(line)
        total_lines += 1
    # read destination edit log
    dest_log = open(os.path.join(dest_dir, 'edit-log'), 'r').readlines()
    print "Merge %d of %d lines from %s/edit-log with %d lines in %s/edit-log" \
      % (len(log), total_lines, source_dir, len(dest_log), dest_dir)
    log += [line.split('\t') for line in dest_log]
    log = sorted(log, cmp=lambda x, y: cmp(x[0], y[0]))
    # write the merged logs
    if not dry_run:
        # backup the existing log
        os.rename(os.path.join(dest_dir, 'edit-log'),
          os.path.join(dest_dir, 'edit-log.bak'))
        dest_logfile = open(os.path.join(dest_dir, 'edit-log'), 'w')
        dest_logfile.writelines(['\t'.join(line) for line in log])
        dest_logfile.close()
    else:
        print 'merge_logs: writing merged edit-log \n\n'
#        print ''.join(['\t'.join(line) for line in log])
#        print '\n\n'
    # read source event log
    log = []
    total_lines = 0
    def decode(s):
        return re.sub(r'\(([^\)]{2,4})\)', lambda m: unichr(int(m.group(1), 16)), s)
    source_pages_plain = [decode(p) for p in source_pages]
    dest_pages_plain = [decode(p) for p in dest_pages]
    pages_plain = zip(source_pages_plain, dest_pages_plain)
    for line in open(os.path.join(source_dir, 'event-log'), 'r').readlines():
        line = line.split('\t')
        if line[1] == 'SAVEPAGE' and any([line[2].find('pagename=' + s) > -1 for s in source_pages_plain]):
            for (old, new) in pages_plain:
                line[2] = line[2].replace(old, new)
            log.append(line)
            print line
        total_lines +=1
    # read destination event log
    dest_log = open(os.path.join(dest_dir, 'event-log'), 'r').readlines()
    print "Merge %d of %d lines from %s/event-log with %d lines in %s/event-log" \
      % (len(log), total_lines, source_dir, len(dest_log), dest_dir)
    log += [line.split('\t') for line in dest_log]
    log = sorted(log, cmp=lambda x, y: cmp(x[0], y[0]))
    # write the merged logs
    if not dry_run:
        # backup the existing log
        os.rename(os.path.join(dest_dir, 'event-log'),
          os.path.join(dest_dir, 'event-log.bak'))
        dest_logfile = open(os.path.join(dest_dir, 'event-log'), 'w')
        dest_logfile.writelines(['\t'.join(line) for line in log])
        dest_logfile.close()
    else:
        print 'merge_logs: writing merged event-log \n\n'


def parse_args():
    """Parse command-line options."""
    parser = OptionParser(usage='usage: %prog [options] pages\n' + __doc__)
    parser.add_option('--user-map', help='read user mappings from FILE',
      metavar='FILE', action='callback', callback=read_map, type='string',
      dest='user_map', default=[])
    parser.add_option('--page-map', help='read page mappings from FILE',
      metavar='FILE', action='callback', callback=read_map, type='string',
      dest='page_map', default=[])
    parser.add_option('--source', help='merge from DIRECTORY',
      metavar='DIRECTORY', dest='source_dir')
    parser.add_option('--dest', help='merge into DIRECTORY',
      metavar='DIRECTORY', dest='dest_dir')
    parser.add_option('-n', '--dry-run', help='dry-run, do not change files',
      metavar='DIRECTORY', action='store_true', dest='dry_run', default=False)
    return parser.parse_args()


def read_map(option, opt, fn, parser):
    """Read user or page name mappings from a file. Callback for parse_args"""
    mappings = [line.rstrip().split('\t') for line in open(fn, 'r').readlines()]
    setattr(parser.values, option.dest, mappings)


if __name__ == '__main__':
    (options, args) = parse_args()
    globals().update(options.__dict__)
    pages = build_page_list(args)
    copy_data(pages)
    merge_logs(pages)
