"""Tools for Obsidian notes."""
# TODO Convert Zim "parent" pages to Obsidian Folder/0_README.md or similar
# TODO Record steps for installing Zim as a Python package from GitHub
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import click
from xdg_base_dirs import xdg_config_home

# TODO Write this to a temporary file instead of requiring it in the notebook/vault dir
TEMPLATE = """[% FOR page IN pages %]
---
imported-from-zim: true
---
# [% page.title %]

[% page.body %]
[% END %]"""


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

        # Construct the Zim notebook
        # Zim internals to access a Notebook object
        from zim import notebook

        info = notebook.resolve_notebook(str(self.path))
        self.zim_notebook, _ = notebook.build_notebook(info)
        self.zim_notebook.index.check_and_update()

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


@click.group("obsidian", help=__doc__)
@click.pass_context
def main(ctx):
    ctx.obj = Config()


def is_zim_note(path: Path) -> bool:
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

    # Path for the Obsidian page
    output_path = path.parent.joinpath(path.name.replace("_", " ")).with_suffix(".md")
    print(f"{path.relative_to(config.path)} → {output_path.relative_to(config.path)}")

    template = config.path.joinpath("Templates", "zim-import.md")

    exporter = build_page_exporter(
        newfs.LocalFile(str(output_path)), "markdown", str(template), zim_page
    )
    if True:
        exporter.export(selection)

    # Tidy Obsidian files that are duplicated by Zim exporter

    obsidian_page_dir = path.with_suffix("")
    obsidian_subpages = set(map(lambda p: p.name, obsidian_page_dir.glob("*.md")))

    output_files_dir = output_path.parent.joinpath(f"{output_path.stem}_files")

    if not output_files_dir.is_dir():
        return

    try:
        N = 0
        for copied in output_files_dir.glob("*"):
            if copied.name in obsidian_subpages:
                N += 1
                copied.unlink()
            else:
                print(f"Zim copied {copied}")
        output_files_dir.rmdir()
    except OSError:
        print(
            f"Zim copied {len(list(output_files_dir.glob('*')))} files to {output_files_dir}"
        )
    else:
        # print(f"Unlinked {N} Obsidian pages copied by Zim")
        pass


def convert_line(line: str) -> str:
    # TODO use backreference
    heading = re.compile("(?P<heading_depth>={1,6}) (.*) ={1,6}\n")
    if match := heading.fullmatch(line):
        hd = match.group("heading_depth")
        line = ("#" * (7 - len(hd))) + f" {match.group(2)}"

    return line


@main.command("from-zim")
@click.pass_obj
def from_zim(config):
    for p in zim_notes(config.path):
        convert_single(config, p)
