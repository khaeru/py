from io import StringIO
from pathlib import Path
from textwrap import wrap

import click
from pybtex.plugin import find_plugin
from pybtex.backends.markdown import Backend
from pybtex.richtext import Text
from pybtex.style.names import BaseNameStyle, name_part
from pybtex.style.formatting import toplevel
from pybtex.style.formatting.unsrt import pages, Style
from pybtex.style.template import (
    node,
    join,
    words,
    field,
    optional,
    first_of,
    # names,
    sentence,
    tag,
    optional_field,
    href,
)


class CustomBackend(Backend):
    symbols = {"ndash": "–", "newblock": " ", "nbsp": " "}

    def write_entry(self, key, label, text):
        wrapped = wrap(text, width=80, initial_indent="- ", subsequent_indent="  ")
        self.output("\n".join(wrapped) + "\n")


MONTHS = {
    "1": "January",
    "2": "February",
    "3": "March",
    "4": "April",
    "5": "May",
    "6": "June",
    "7": "July",
    "8": "August",
    "9": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}


@node
def date(children, data, type="article"):

    assert not children
    if type == "event":
        return data.rich_fields["eventdate"]
    elif type == "report":
        return Text(MONTHS[data.fields["month"]]) + Text(" ") + data.rich_fields["year"]
    else:
        return data.rich_fields["year"]


class ConciseNameStyle(BaseNameStyle):
    def __init__(self):
        self._seen = set()

    def format(self, person, *args):
        abbr = repr(person) in self._seen
        self._seen.add(repr(person))
        return join[
            name_part(tie=True, abbr=abbr)[
                person.rich_first_names + person.rich_middle_names
            ],
            name_part(tie=True)[person.rich_prelast_names],
            name_part[person.rich_last_names],
            name_part(before=", ")[person.rich_lineage_names],
        ]


class BibLaTeXStyle(Style):
    default_name_style = ConciseNameStyle

    def format_event_venue_date(self, e, enclose=None):
        result = join(sep=", ")[field("venue"), date("event")]
        if enclose is not None:
            result = join[enclose[0], result, enclose[1]]
        return result

    def format_article(self, e):
        volume_and_pages = first_of[
            # volume and pages, with optional issue number
            optional[
                join[field("volume"), optional["(", field("number"), ")"], ":", pages],
            ],
            # pages only
            words["pages", pages],
        ]
        template = toplevel[
            sentence(sep=" ")[
                self.format_names("author", False),
                join["(", date, ")"],
            ],
            join["“", self.format_title(e, "title"), "”"],
            sentence[
                tag("em")[first_of[field("journaltitle"), field("journal")]],
                optional[volume_and_pages],
            ],
            sentence[optional_field("note")],
            self.format_web_refs(e),
        ]
        return template.format_data(e)

    def format_eprint(self, e):
        # based on urlbst format.eprint
        return href[
            join["http://hdl.handle.net/", field("eprint")],
            join["HDL: ", field("eprint")],
        ]

    def format_inproceedings(self, e):
        template = toplevel[
            sentence[self.format_names("author")],
            self.format_title(e, "title"),
            words[
                "In:",
                sentence(sep=" ")[
                    first_of[
                        field("eventtitle"),
                        join[
                            optional[self.format_editor(e, as_sentence=False)],
                            self.format_btitle(e, "booktitle", as_sentence=False),
                            self.format_volume_and_series(e, as_sentence=False),
                            optional[pages],
                        ],
                    ],
                    self.format_event_venue_date(e, "()"),
                ],
            ],
            sentence[optional_field("organization")],
            sentence[optional_field("note")],
            self.format_web_refs(e),
        ]
        return template.format_data(e)

    def format_report(self, e):
        return self.format_techreport(e)

    def format_techreport(self, e):
        template = toplevel[
            sentence(sep=" ")[
                self.format_names("author", False),
                join["(", date("report"), ")"],
            ],
            self.format_title(e, "title"),
            sentence[
                words[
                    first_of[
                        optional_field("type"),
                    ],
                    optional_field("number"),
                ],
                field("institution"),
                optional_field("address"),
            ],
            sentence[optional_field("note")],
            self.format_web_refs(e),
        ]
        return template.format_data(e)


Parser = find_plugin("pybtex.database.input", None)


def make_bibliography(title, keys, files, style, backend, stream):
    bib_data = Parser(wanted_entries=keys).parse_files(files)
    formatted = style.format_bibliography(bib_data, keys)
    stream.write("## %s\n\n" % title)
    backend.write_to_stream(formatted, stream)
    stream.write("\n")


@click.command()
@click.argument("bibfile")
@click.argument("path", type=Path)
def cli(bibfile, path):
    path = path.resolve()

    if not path.suffix.endswith(".in"):
        raise click.ClickException(f"Input path does not end with '.in': {repr(path)}")

    target = path.with_suffix(path.suffix[:-3])
    print(f"Write to {target}")

    bibs = path.read_text()

    style = BibLaTeXStyle()
    backend = CustomBackend()
    result = StringIO()

    extra_keys = ["tr:d", "trr"]

    for title, keys in bibs.items():
        make_bibliography(title, keys + extra_keys, [bibfile], style, backend, result)

    print(result.getvalue().replace("$\\_2$", "₂"))


if __name__ == "__main__":
    cli()
