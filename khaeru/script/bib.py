#!/usr/bin/env python3
import argparse
import os
import os.path
import re

import bibtexparser
from bibtexparser.bparser import BibTexParser

#with open('test.bib', 'w') as of:
#    for key, record in bp.get_entry_dict().items():
#        type_ = record.pop('type')
#        id_ = record.pop('id')
#        data = '",\n\t'.join(['{} = "{}'.format(k, v) for k, v in record.items()])
#        entry = """@{}{{{},\n\t{}"\n}}\n""".format(id_, type_, data)
#        of.write(entry)

KW_SEP = ',|;'
keywords = set()


class BibItem(dict):
    def __init__(self, record):
        try:
            record['keywords'] = [k.strip() for k in
                                  re.split(KW_SEP, record['keywords'])]
            keywords.update(record['keywords'])
        except KeyError:
            pass
        dict.__init__(self, record)
        self.type = self['type']

    @property
    def has_file(self):
        return 'localfile' in self

    @property
    def file_exists(self):
        return os.path.exists(self['localfile'])

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
        # Set up argument parsing
        ap = argparse.ArgumentParser()
        ap.add_argument('command',
                        choices=['check-files','kw-list','queue'],
                        default='kw-list',
                        help='Commands!')
        ap.add_argument('infile', type=open, help='BibTeX database to read.')
        self.argument_parser = ap

    def main(self):
        self.args = self.argument_parser.parse_args()

        parser = BibTexParser()
        parser.homogenise_fields = False
        parser.ignore_nonstandard_types = False
        parser.customization = lambda r: BibItem(r)
        self.db = bibtexparser.load(self.args.infile, parser=parser)

        getattr(self, self.args.command.replace('-', '_'))()

    def _get_entry_by_id(self, entry_id):
        for e in self.db.entries:
            if e['id'] == entry_id:
                return e

    def kw_list(self):
        print('\n'.join(sorted(keywords)))

    def check_files(self):
        ok = set()
        missing = set()
        broken = set()
        # get the set of files in the current directory
        ignore = set([
            '.git',
            '.gitignore',
            '.rsync-filter',
            'all.bib',
            'README',
            ])
        files = set(filter(lambda x: not os.path.isdir(x),
                  os.listdir('.'))).difference(ignore)
        for e in self.db.entries:
            if e.has_file:
                if e.file_exists:
                    ok.add(e['id'])
                    files.remove(e['localfile'].lstrip('./'))
                else:
                    broken.add((e['id'], e['localfile']))
            else:
                missing.add(e['id'])
        print('OK (localfile key refers to an existing file):\n\t',
              ' '.join(sorted(ok)))
        print('\nMissing (localfile key is absent):\n\t',
              ' '.join(sorted(missing)))
        print('\nBroken (localfile key refers to a non-existent file):')
        for e in sorted(broken):
            print('{}\n\t{}'.format(*e))
        print('\nFiles not listed in any entry:\n\t',
              '\n\t'.join(sorted(files)))

    def queue(self):
        # TODO implement x-pnk:queue-omit
        # TODO implement x-pnk:queue-read
        no_kw = set()
        no_tag = set()
        my_tags = set()
        print("\nRead next (has keyword 'x-pnk:queue-to-read'):")
        for e in self.db.entries:
            try:
                if 'x-pnk:queue-to-read' in e['keywords']:
                    print('\t{}: {}\n\t\t{}'.format(e['id'], e['title'],
                                                  e['localfile']))
                elif any([('x-pnk:' in kw) for kw in e['keywords']]):
                    my_tags.add(e['id'])
                else:
                    no_tag.add(e['id'])
            except KeyError:
                no_kw.add(e['id'])
                continue
        print("\nHas no 'x-pnk:' keyword:\n\t",
              ' '.join(sorted(no_tag)))
        print('\nNo keywords whatsoever:\n\t', ' '.join(sorted(no_kw)))
        print("\nHas some other 'x-pnk:' keyword:\n\t",
              ' '.join(sorted(my_tags)))
        print()


if __name__ == '__main__':
    BibApp().main()
