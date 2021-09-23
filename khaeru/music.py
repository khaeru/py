"""Manage a music collection."""
import re
import subprocess
import sys
from functools import partial
from pathlib import Path

import click
from tqdm import tqdm

# Mapping from regular expression to action for handling the file. False = skip.
ACTIONS = {
    re.compile(r"\.(cue|log|m3u|txt|sh)$", flags=re.IGNORECASE): False,
    # Others that should be cleaned up
    re.compile(r"/\.DS_Store$"): False,
    # Internal catalogue
    re.compile(r"/(cue|log|LEGAL)$"): False,
    # New items not fully added to library
    re.compile(r"/#[^/]*/"): False,
}


@click.group(name="music", help=__doc__)
def cli():
    pass


PATH_TYPE = click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path)


@cli.command("convert")
@click.pass_context
@click.option("--dry-run", is_flag=True, help="Only show what would be done.")
@click.option("--exclude-from", default="k-mobile-rsync.txt")
@click.argument("src", type=PATH_TYPE)
@click.argument("dest", type=PATH_TYPE)
def convert_cmd(ctx, src, dest, dry_run, exclude_from):
    """Convert files."""

    # Add exclusions first, before matching on extensions etc.
    read_rsync_filters(src.joinpath(exclude_from))

    ACTIONS.update(
        {
            # Convert these formats
            re.compile(r"\.(flac|wav)$"): convert,
            # Symlink these; change to False to disable
            re.compile(r"\.mp3$"): False,  # symlink,
            re.compile("/album.jpe?g$"): False,  # symlink,
            # Skip other JPEG files
            re.compile(".jpe?g$"): False,
            # Flag value / matches everything
            re.compile("."): None,
        }
    )

    # Iterate over files
    for path in tqdm(sorted(src.rglob("*"))):
        # Skip directories
        if not path.is_file():
            continue

        # Destination path
        dest_path = dest / path.relative_to(src)

        # Identify an action to handle this path by looking for a regex match
        for pattern, func in ACTIONS.items():
            if pattern.search(str(path)):
                break

        if func is False:
            continue  # Skip silently
        elif func is None:
            print(
                "No action for file name/suffix: "
                f"{path.suffix if len(path.suffix) else path.name}"
                f"in {path.parent.relative_to(src)}"
            )
            continue

        # Apply the action
        func(path, dest_path, dry_run)


def read_rsync_filters(exclude_from: Path) -> list[re.Pattern]:
    """Read exclusion filters from an rsync-formatted filters file `exclude_from`."""
    for op, pattern in filter(
        lambda e: len(e) == 2,
        map(
            partial(str.split, maxsplit=1),
            exclude_from.read_text().split("\n"),
        ),
    ):
        if op != "-":
            continue  # Not an exclusion pattern: comment, inclusion, something else

        try:
            ACTIONS[re.compile(pattern.rstrip())] = False
        except re.error:
            pass


def convert(path, dest, dry_run):
    """Convert to Opus format."""
    # Use .opus suffix on destination path
    dest = dest.with_suffix(".opus")

    if dest.exists():
        print(f"File exists; delete to re-convert: {dest}")
        return

    # TODO make this configurable
    # bitrate = 256 if "Classical" in dest else 160
    bitrate = 256

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-codec:a",
        "libopus",
        "-b:a",
        f"{bitrate}k",
        str(dest),
    ]

    if dry_run:
        print(" ".join(cmd))
    else:
        dest.parent.mkdir(exist_ok=True, parents=True)

        # Pipe live output to terminal
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for c in iter(lambda: process.stdout.read(1), b""):
            sys.stdout.write(c)


def symlink(path, dest, dry_run):
    if dry_run:
        print(f"Symlink {dest} → {path}")
    else:
        dest.parent.mkdir(exist_ok=True, parents=True)
        dest.symlink_to(path)
