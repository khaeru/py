#!/usr/bin/env python3.5
"""BibTeX database utilities
© 2016 Paul Natsuo Kishimoto <mail@paul.kishimoto.name>
Licensed under the GNU GPL v3.
"""
import argparse
from glob import iglob
from itertools import filterfalse, zip_longest
import os
import os.path
import re

import bibtexparser
from bibtexparser.bparser import BibTexParser
import yaml


DEFAULT_CONFIG = {
    'kw_sep': ',|;',
    'lf_sep': ';',
    }


class BibItem(dict):
    """Biliography items."""

    def __init__(self, record, add_keywords, config):
        # Parse 'keywords' to a list
        if 'keywords' in record:
            record['keywords'] = [kw.strip() for kw in
                                  re.split(config['kw_sep'],
                                           record['keywords'])]
            add_keywords(record['keywords'])

        # Parse 'localfile' to a list
        if 'localfile' in record:
            record['localfile'] = [lf.strip() for lf in
                                   re.split(config['lf_sep'],
                                            record['localfile'])]

        dict.__init__(self, record)
        self.type = self['ENTRYTYPE']

    @property
    def has_file(self):
        return 'localfile' in self

    @property
    def file_exists(self):
        if type(self['localfile']) == list:
            return all([os.path.exists(lf) for lf in self['localfile']])
        else:
            return os.path.exists(self['localfile'])

    def file_rel_path(self):
        if type(self['localfile']) == list:
            return [os.path.relpath(lf) for lf in self['localfile']]
        else:
            return os.path.relpath(self['localfile'])

    def stringify(self):
        """Convert all entries to strings.

        bibtexparser.bwriter.BibTexWriter requires all records in an item
        to be strings.
        """
        try:
            self['keywords'] = ';'.join(self['keywords'])
        except KeyError:
            pass


class BibApp:
    def __init__(self):
        self.config = DEFAULT_CONFIG
        try:
            with open('.bibpy.yaml') as f:
                self.config.update(yaml.load(f))
        except FileNotFoundError:
            pass

        self.keywords = set()
        self.commands = ['check-files', 'kw-list', 'queue', 'help']

        # Set up argument parsing
        ap = argparse.ArgumentParser(
            description=self._help(),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        ap.add_argument('--verbose', '-v', action='store_true')
        ap.add_argument('command',
                        choices=self.commands,
                        default='kw-list',
                        metavar='COMMAND')
        ap.add_argument('infile',
                        nargs='?',
                        type=open,
                        help='BibTeX database to read.',
                        default=self.config.get('database', None))
        self.argument_parser = ap

    def main(self):
        # Parse arguments
        self.args = self.argument_parser.parse_args()
        self.verbose = self.args.verbose

        # Set up the BibTeX parser
        parser = BibTexParser()
        parser.homogenise_fields = False
        parser.ignore_nonstandard_types = False
        parser.customization = lambda r: BibItem(r,
                                                 self.keywords.update,
                                                 self.config)
        # Parse the database
        self.db = bibtexparser.load(self.args.infile, parser=parser)

        # Invoke the command chosen by the user
        command = getattr(self, self.args.command.replace('-', '_'))
        args = self.config.get(self.args.command, {})
        command(**args)

    def help(self):
        """Show help for commands."""
        lines = []
        for cmd in self.commands:
            method = cmd.replace('-', '_')
            docstring = getattr(self, method).__doc__
            lines.append('{}\n\t{}'.format(cmd, docstring))
        print('\n\n'.join(lines))

    def _help(self):
        lines = [__doc__, '', 'Commands:']
        width = max(map(len, self.commands))
        for cmd in self.commands:
            method = cmd.replace('-', '_')
            docstring = getattr(self, method).__doc__
            lines.append('  {0:{width}}\t{1}'.format(
                cmd, docstring.splitlines()[0], width=width))
        return '\n'.join(lines)

    def kw_list(self):
        """List all keywords appearing in entries."""
        print('\n'.join(sorted(self.keywords)))

    def check_files(self, **kwargs):
        """Check files listed with the 'localfiles' fields."""
        # Get configuration options
        ignore = kwargs.get('ignore', [])
        filters = kwargs.get('filter', [])

        # Sets for recording entries:
        # - ok: has 'localfile' field, file exists
        # - other: hardcopies or online articles
        # - missing: no 'localfile' field
        # - broken: 'localfile' field exists, but is wrong
        sets = {k: set() for k in ['ok', 'other', 'missing', 'broken']}

        # Get the set of files in the current directory
        r = re.compile('(' + ')|('.join(ignore) + ')')
        files = filterfalse(os.path.isdir, iglob('**', recursive=True))
        files = sorted(filterfalse(r.search, files))

        # Iterate through database entries
        for e in self.db.entries:
            if e.has_file:
                if e.file_exists:
                    sets['ok'].add(e['ID'])
                    for fn in e.file_rel_path():
                        files.remove(fn)
                else:
                    sets['broken'] |= {(e['ID'], lf) for lf in e['localfile']}
            else:
                # Apply user filters
                done = False
                for f in filters:
                    if f['field'] in e and f['value'] in e[f['field']]:
                        sets[f['sort']].add(e['ID'])
                        done = True
                        break
                if not done:
                    sets['missing'].add(e['ID'])

        # Output
        output_format = kwargs.get('format', 'plain')
        if output_format == 'plain':
            output = self._check_files_plain
        elif output_format == 'csv':
            output = self._check_files_csv
        output(sorted(sets['ok']), sorted(sets['other']),
               sorted(sets['missing']), sorted(sets['broken']),
               files)

    def _check_files_plain(self, ok, other, missing, broken, files):
        print('OK: %d entries + matching files' % len(ok),
              '\t' + ' '.join(sorted(ok)),
              '',
              'OK: %d other entries by filter rules' % len(other),
              '\t' + ' '.join(sorted(other)),
              '',
              "Missing: %d entries w/o 'localfile' key" % len(missing),
              '\t' + '\n\t'.join(sorted(missing)),
              '',
              "Broken: %d entries w/ missing 'localfile'" % len(broken),
              '\n'.join(['\t{}\t→\t{}'.format(*e) for e in sorted(broken)]),
              '',
              'Not listed in any entry: %d files' % len(files),
              '\t' + '\n\t'.join(sorted(files)),
              sep='\n', end='\n')

    def _check_files_csv(self, ok, other, missing, broken, files):
        lines = ['\t'.join(['ok', 'other', 'missing', 'broken', 'files'])]
        for group in zip_longest(ok, other, missing, broken, files,
                                 fillvalue=''):
            lines.append('\t'.join(group))
        print('\n'.join(lines))

    def queue(self, **kwargs):
        """Display a reading queue.

        The configuration value queue/include should contain a regular
        expression with one match group named 'priority'.

        When this matches against the keywords of a database entry, the
        entry is considered to be part of a reading queue, sorted from lowest
        to highest according to priority.

        With --verbose/-v, *queue* also displays list of entries with no
        keywords; and with keywords but no queue match.
        """
        r = re.compile(kwargs.get('include', None))

        sets = {'no_kw': set(), 'no_queue': set(), 'to_read': list()}

        for e in self.db.entries:
            if 'keywords' in e:
                matches = list(filter(None,
                                      [r.match(kw) for kw in e['keywords']]))
                if len(matches) > 1:
                    assert False
                elif len(matches) == 1:
                    pri = matches[0].groupdict()['priority']
                    sets['to_read'].append(('({0}) {1[ID]}: {1[title]}\n\t'
                                            '{1[localfile]}').format(pri, e))
                else:
                    sets['no_queue'].add(e['ID'])
            else:
                sets['no_kw'].add(e['ID'])

        if self.verbose:
            print('No keywords: %d entries' % len(sets['no_kw']),
                  '\t' + ' '.join(sorted(sets['no_kw'])),
                  '',
                  'Some keywords: %d entries' % len(sets['no_queue']),
                  '\t' + ' '.join(sorted(sets['no_queue'])),
                  sep='\n', end='\n\n')

        print('Read next:',
              '\n'.join(sorted(sets['to_read'])),
              sep='\n', end='\n\n')


if __name__ == '__main__':
    BibApp().main()
