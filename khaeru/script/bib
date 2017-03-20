#!/usr/bin/env python3
"""BibTeX database utilities
© 2016–2017 Paul Natsuo Kishimoto <mail@paul.kishimoto.name>
Licensed under the GNU GPL v3.
"""
from collections import namedtuple
from glob import iglob
from itertools import filterfalse, zip_longest
import os
import os.path
import re

import bibtexparser
# import bibtexparser.customization as btp
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
import click
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


class BibCLIContext:
    def __init__(self):
        self.config = DEFAULT_CONFIG
        try:
            with open('.bibpy.yaml') as f:
                self.config.update(yaml.load(f))
        except FileNotFoundError:
            pass

        self.keywords = set()

    def init(self, database, verbose):
        # # Parse arguments
        # self.args = self.argument_parser.parse_args()
        self.verbose = verbose

        # Set up the BibTeX parser
        parser = BibTexParser()
        parser.homogenise_fields = False
        parser.ignore_nonstandard_types = False
        parser.customization = lambda r: BibItem(r,
                                                 self.keywords.update,
                                                 self.config)
        # Parse the database
        self.db = bibtexparser.load(open(database, 'r'), parser=parser)

    def cmd_config(self, cmd):
        return self.config.get(cmd, {})


# Custom decorator that uses BibCLIContext
pass_context = click.make_pass_decorator(BibCLIContext, ensure=True)


@pass_context
def default_db(ctx):
    """Return the default database path."""
    return ctx.config.get('database', None)


@click.group(help=__doc__)
@click.option('--database', type=click.Path('r'), default=default_db)
@click.option('--verbose', is_flag=True, help='More detailed output.')
@pass_context
def cli(ctx, database, verbose):
    # Initialize the context (load the database)
    ctx.init(database, verbose)


def _add_clean(d):
    """Custom entry cleaning for add()."""

    # Delete the leading text 'ABSTRACT'
    if 'abstract' in d and d['abstract'].lower().startswith('abstract'):
        d['abstract'] = d['abstract'][8:].strip()

    d['author'] = d['author'].replace('\n', ' ')

    if 'doi' in d:
        # Show a bare DOI, not a URL
        d['doi'] = d['doi'].replace('http://dx.doi.org/', '')
        # Don't show eprint or url fields if a DOI is present
        # (e.g ScienceDirect)
        d.pop('eprint', None)
        d.pop('url', None)

    # BibLaTeX: use 'journaltitle' for the name of the journal
    if 'journal' in d:
        d['journaltitle'] = d.pop('journal')

    if 'pages' in d:
        # Pages: use an en-dash
        d['pages'] = d['pages'].replace('--', '–').replace('-', '–') \
                               .replace(' ', '')

    # Delete any empty fields or those containing '0'
    for k in list(d.keys()):
        if d[k] in ['0', '']:
            del d[k]

    return d


@cli.command(name='import')
@pass_context
def import_entries(ctx):
    """(DEV) Read new entries into the database."""
    # Directory from which to import entries
    add_dir = ctx.cmd_config('add').get('path', 'import')

    # A parser for reading entries
    parser = BibTexParser()
    parser.homogenise_fields = False
    parser.customization = _add_clean

    # A writer for converting entries back to strings
    writer = BibTexWriter()

    # namedtuple to imitate a class with these attributes
    _dbnt = namedtuple('bdb', ['comments', 'entries', 'preambles', 'strings'])

    def to_string(entry):
        """Convert [entry] to a string."""
        # Create a fake 'database' with only one writer.
        return writer.write(_dbnt([], [entry], [], {}))

    # File for imported entries
    f_imported = open('added.bib', 'a')

    # Iterate over files in the add_dir
    for fn in iglob(os.path.join(add_dir, '*.bib')):
        os.system('clear')
        print('Importing', fn, end='\n\n')

        # Read and parse the file
        with open(fn, 'r') as f:
            s = f.read()
            e = parser.parse(s).entries[0]
            abstract = e.pop('abstract', None)

        print('Raw:', s)
        print('Entry:', to_string(e), sep='\n\n')

        if abstract is not None:
            print('Abstract:', abstract, sep='\n\n')

        # Ask user for a key
        while True:
            key = input('\nEnter key for imported entry '
                        '([Enter] to skip, [Q]uit): ')
            if key in ctx.db.entries_dict:
                print('Key already exists.')
            else:
                break

        if key == '':
            continue
        elif key.lower() == 'q':
            break
        else:
            # Change the entry key
            e['ID'] = key

        if abstract is not None:
            fn_abs = os.path.join('abstracts', '%s.tex' % key)
            with open(fn_abs, 'x') as f_abs:
                f_abs.write(abstract)

        f_imported.write(to_string(e))

        # Remove the imported file
        remove = input('\nRemove imported file %s ([Y]es, [enter] to keep)? '
                       % fn)
        if remove.lower() == 'y':
            os.remove(fn)


def _check_files_plain(ok, other, missing, broken, files):
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


def _check_files_csv(ok, other, missing, broken, files):
    lines = ['\t'.join(['ok', 'other', 'missing', 'broken', 'files'])]
    for group in zip_longest(ok, other, missing,
                             map(lambda x: '{} -> {}'.format(*x), broken),
                             files, fillvalue=''):
        lines.append('\t'.join(group))
    print('\n'.join(lines))


@cli.command()
@click.option('--format', 'fmt', type=click.Choice(['plain', 'csv']),
              default=None)
@pass_context
def check_files(ctx, fmt):
    """Check files listed with the 'localfiles' fields."""
    # Get configuration options
    options = ctx.cmd_config('check-files')
    ignore = options.get('ignore', [])
    filters = options.get('filter', [])

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
    for e in ctx.db.entries:
        if e.has_file:
            if e.file_exists:
                sets['ok'].add(e['ID'])
                for fn in e.file_rel_path():
                    try:
                        files.remove(fn)
                    except ValueError:
                        if os.path.exists(fn):
                            # File exists, but has perhaps been filtered or
                            # is outside the tree.
                            continue
                        else:
                            raise
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
    output_format = options.get('format', 'csv') if fmt is None else fmt
    if output_format == 'plain':
        output = _check_files_plain
    elif output_format == 'csv':
        output = _check_files_csv
    output(sorted(sets['ok']), sorted(sets['other']),
           sorted(sets['missing']), sorted(sets['broken']),
           files)


@cli.command()
@pass_context
def kw_list(ctx):
    """List all keywords appearing in entries."""
    print('\n'.join(sorted(ctx.keywords)))


@cli.command()
@pass_context
def queue(ctx):
    """Display a reading queue.

    The configuration value queue/include should contain a regular
    expression with one match group named 'priority'.

    When this matches against the keywords of a database entry, the
    entry is considered to be part of a reading queue, sorted from lowest
    to highest according to priority.

    With --verbose/-v, *queue* also displays list of entries with no
    keywords; and with keywords but no queue match.
    """
    r = re.compile(ctx.cmd_config('queue').get('include', None))

    sets = {'no_kw': set(), 'no_queue': set(), 'to_read': list()}

    for e in ctx.db.entries:
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

    if ctx.verbose:
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
    cli()
