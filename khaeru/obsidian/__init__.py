"""Obsidian notes."""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import click
from xdg_base_dirs import xdg_config_home


@dataclass
class Config:
    config: dict = field(default_factory=dict)

    path: Optional[Path] = None

    def __post_init__(self):
        p = xdg_config_home().joinpath("obsidian", "obsidian.json")
        with open(p) as f:
            self.config = json.load(f)

        assert 1 == len(self.config["vaults"])
        vault = next(iter(self.config["vaults"].keys()))
        self.path = Path(self.config["vaults"][vault]["path"])


@click.group("obsidian", help=__doc__)
@click.pass_context
def main(ctx):
    ctx.obj = Config()


def convert_single(path: Path):
    with open(path) as f:
        for line in f:
            print(line, convert_line(line), sep="")


def convert_line(line: str) -> str:
    # TODO use backreference
    heading = re.compile("(?P<heading_depth>={1,6}) (.*) ={1,6}\n")
    if match := heading.fullmatch(line):
        hd = match.group("heading_depth")
        line = ("#" * (7 - len(hd))) + f" {match.group(2)}"

    return line


@main.command("from-zim")
@click.argument("name")
@click.pass_obj
def from_zim(ctx, name):
    d = ctx.path
    matches = list(d.glob(f"**/*{name}*.txt"))
    if len(matches) == 0:
        raise ValueError("No matches")
    elif len(matches) > 1:
        raise ValueError("Ambiguous:\n" + "\n".join(map(str, matches)))
    p = matches[0]
    convert_single(p)
