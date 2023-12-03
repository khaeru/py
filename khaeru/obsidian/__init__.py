"""Tools for Obsidian notes.

This requires installing Zim via pip. To do this:

\b
1. Follow the Ubuntu / pip install instructions at
   https://pygobject.readthedocs.io/en/latest/getting_started.html to install "gi".
2. pip install --no-build-isolation \
     zim @ git+https://github.com/zim-desktop-wiki/zim-desktop-wiki"
"""
# To undo while debugging, something like:
# $ git ls-files --others --exclude-standard -z | xargs -0 rm
#

import filecmp
import json
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

import click
from xdg_base_dirs import xdg_config_home

# Zim template
TEMPLATE = """[% FOR page IN pages %]
---
zim-imported: true
zim-creation-date: [% page.meta.get("Creation-Date") %]
---
# [% page.title %]

[% page.body %]

[% SET needs_attachments_header = True %]

[% FOREACH a = page.attachments %]
[% IF not a.basename.endswith(".md") %]
[% IF needs_attachments_header %]
## Attachments (imported from Zim)
[% SET needs_attachments_header = False %]

[% END %]
![[[% a.basename %]]] [% END %][% END %]
[% END %]
"""


@dataclass
class Config:
    """Access Obsidian configuration."""

    #: Contents of the Obsidian config file.
    config: dict = field(default_factory=dict)

    #: Path to the first/default vault.
    path: Optional[Path] = None

    def __post_init__(self):
        p = xdg_config_home().joinpath("obsidian", "obsidian.json")
        with open(p) as f:
            self.config = json.load(f)

        # Identify the Obsidian vault
        assert 1 == len(self.config["vaults"])
        vault = next(iter(self.config["vaults"].keys()))
        self.path = Path(self.config["vaults"][vault]["path"])

        # Write the template file
        template_path = self.path.joinpath("Templates", "zim-import.md")
        template_path.write_text(TEMPLATE)
        self.template = str(template_path)

        # Construct the Zim notebook object, imitating internals of zim.export
        from zim import notebook

        info = notebook.resolve_notebook(str(self.path))
        self.zim_notebook, _ = notebook.build_notebook(info)
        self.zim_notebook.index.check_and_update()

        # Create a temporary directory for conversion
        self._tmp_dir = TemporaryDirectory()
        self.tmp = Path(self._tmp_dir.name)

    def zim_page(self, path):
        """Construct and return a Zim Page object."""
        from zim import notebook
        from zim.export.selections import SinglePage

        zim_path = notebook.Path(str(path.relative_to(self.path).with_suffix("")))
        zim_page = self.zim_notebook.get_page(zim_path)
        if not zim_page.exists():
            print(f"No {zim_page = } for {path}; skip")
            return None, None

        selection = SinglePage(self.zim_notebook, zim_page)

        return zim_page, selection


def is_zim_note(path: Path) -> bool:
    """Return :obj:`True` if `path` is a Zim note file."""
    with open(path, "r") as f:
        return "Content-Type: text/x-zim-wiki" == next(f).strip()


def zim_notes(path: Path):
    """Iterate over Zim notes in `path`."""
    for p in sorted(path.glob("**/*.txt")):
        if not is_zim_note(p):
            print(f"File appears not to be a Zim note: {p}")
            continue
        yield p


def convert_single(config: Config, path: Path):
    """Convert a single Zim note to Obsidian Markdown."""
    from zim import newfs
    from zim.export import build_page_exporter

    # Retrieve a Zim page object
    zim_page, selection = config.zim_page(path)

    if zim_page is None:
        print(f"No {zim_page = } for {path}; skip")
        return

    # Subdirectory for the Obsidian page
    obsidian_page_dir = path.with_suffix("")

    # Path relative to the base directory
    rel_path = path.relative_to(config.path)

    # Path for Zim export, within a temporary directory
    output_path_zim = config.tmp.joinpath(rel_path).with_suffix(".md")

    # Final output path, with replacements
    output_path_final = config.path.joinpath(
        *map(lambda part: part.replace("_", " "), rel_path.parts)
    ).with_suffix(".md")

    # String for displaying information about this conversion
    msg = f"{path.relative_to(config.path)} → {output_path_zim}"

    # Use Zim to convert the file to Markdown
    output_path_zim.parent.mkdir(parents=True, exist_ok=True)
    exporter = build_page_exporter(
        newfs.LocalFile(str(output_path_zim)), "markdown", config.template, zim_page
    )
    exporter.export(selection)

    # Assert that files duplicated by Zim exporter are not different from those
    # remaining in the Zim tree
    output_files_dir = output_path_zim.parent.joinpath(f"{output_path_zim.stem}_files")
    try:
        for copied in output_files_dir.glob("*"):
            assert filecmp.cmp(
                copied, obsidian_page_dir.joinpath(copied.name), shallow=True
            )
    except FileNotFoundError:
        pass  # No output_files_dir

    # Copy from zim.export output name to the preferred output name
    output_path_zim.rename(output_path_final)

    # Unlink the original Zim file
    path.unlink()

    del msg


# Command-line interface


@click.group("obsidian", help=__doc__)
@click.pass_context
def main(ctx):
    ctx.obj = Config()


@main.command("from-zim")
@click.pass_obj
def from_zim(config):
    for p in zim_notes(config.path):
        convert_single(config, p)
