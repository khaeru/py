"""Personal information management utility."""
import re
from glob import glob
from os.path import expanduser, join
from pathlib import Path
from subprocess import CalledProcessError, call, check_call, check_output

import click
from xdg.BaseDirectory import xdg_config_home, xdg_data_home

from .task import client as task_client, show_slack


CLAWS_CACHE = (
    Path(xdg_data_home)
    .joinpath("claws-mail/imapcache/imap.fastmail.com/khaeru@fastmail.com")
    .expanduser()
)


@click.group(help=__doc__, invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        status()


cli.add_command(click.Command("slack", callback=show_slack, help=show_slack.__doc__))


@cli.command()
@click.argument("task_ids", metavar="IDS", nargs=-1)
def slip(task_ids):
    """Amount that task(s) IDS have been postponed."""
    from .task import show_slip

    show_slip(map(task_client.uuid, task_ids) if len(task_ids) else task_client.uuids())


@cli.command("read")
@click.argument("key")
@click.option(
    "--no-file", is_flag=True, help="Continue even if there is no local file."
)
@click.option(
    "--note/--no-note",
    "create_note",
    default=False,
    help="Create and/or open a Zim note (default: no).",
)
@click.option(
    "--timer", "start_timer", is_flag=True, help="Start tracking with timewarrior."
)
def read_command(key, no_file, create_note, start_timer):
    """Read the article for bibliography entry KEY."""
    from configparser import ConfigParser
    from os.path import exists, expanduser, join

    result = call(["bib", "read", key])

    if result > 0 and not no_file:
        return

    # Read the Zim configuration
    zim_config_path = join(xdg_config_home, "zim", "notebooks.list")
    with open(zim_config_path, "r") as f:
        zim_config = ConfigParser()
        zim_config.read_file(f)

    # Path to the notebook contents
    notes_path = expanduser(zim_config["NotebookList"]["1"])
    # Path to the note assciated with KEY (may not exist)
    note_path = join(notes_path, "Reading_notes", "{}.txt".format(key))
    # Name of the notebook
    notebook = zim_config["Notebook 1"]["name"]
    # Name of the note associated with KEY (may not exist)
    note = "Reading notes:{}".format(key)

    if exists(note_path):
        # Note exists; open it
        call(["zim", notebook, note])
    else:
        if not create_note:
            # Note doesn't exist; user doesn't want to create it
            print("No note.")
        else:
            print("Creating note in {}".format(note_path))
            with open(note_path, "wb") as f:
                # Use the bib script to get a template for the note
                f.write(check_output(["bib", "note_template", key]))

            # Open the note
            call(["zim", notebook, note])

    # Start timewarrior, if desired
    if start_timer:
        call(["timew", "start", "Reading", key])


@cli.command()
def weeklog():
    """Weekly log."""
    info = [
        "Completed tasks:",
        check_output(["task", "+COMPLETED", "end.after:socw", "all"], text=True),
        "Time worked:",
        check_output(["timew", "summary", "sow", "-", "now"], text=True),
        "Untracked gaps:",
        check_output(["timew", "gaps", "sow", "-", "now"], text=True),
    ]

    print("\n".join(info))


@cli.command()
def sent():
    """Compare # of sent e-mails by day of the year.

    E-mails in the Claws Mail IMAP cache for folders named Sent/[year] folder are
    counted by day of year, with cumulative totals displayed for the current and
    previous years.

    If messages are not cached locally, they are not counted. Empty years, and messages
    with Unicode errors, malformatted dates, or no 'Date:' header are skipped.
    """
    from collections import defaultdict
    from datetime import datetime

    import pandas as pd

    time_formats = [
        "Date: %a, %d %b %Y %H:%M:%S %z",
        "Date: %a, %d %b %Y %H:%M:%S %z (%Z)",
    ]

    def count_year(year=""):
        count = defaultdict(int)

        messages = glob(join(CLAWS_CACHE, "Sent", year, "*"))

        if len(messages) == 0:
            return

        for message in messages:
            try:
                for line in open(message):
                    if line.startswith("Date:"):
                        for tf in time_formats:
                            try:
                                date = datetime.strptime(line.strip(), tf)
                                break
                            except ValueError:
                                continue
                        count[date.strftime("%j")] += 1
                        break
            except (IsADirectoryError, UnicodeDecodeError):
                continue

        result = pd.Series(count)
        result.name = year if year != "" else "Current"

        print("{} ({})".format(result.name, len(messages)), end=", ")
        return result

    print("Counting: ", end="")
    year_counts = [count_year(str(y)) for y in range(2004, 2018)]
    year_counts.append(count_year())
    print("done.")

    all_counts = (
        pd.concat(year_counts, axis=1)
        .cumsum()
        .fillna(method="ffill")
        .fillna(value=0)
        .astype(int)
    )

    print("\nMessages sent by this day in…")
    print(all_counts.loc[datetime.today().strftime("%j"), :])


def _count_mail():
    exclude = [".claws_cache", ".claws_mark"]
    counts = []
    for dir in (CLAWS_CACHE / "INBOX", CLAWS_CACHE / "0 List traffic"):
        counts.append(
            sum(
                int(path.is_file() and path.name not in exclude)
                for path in dir.iterdir()
            )
        )
    return counts


@cli.command()
@click.pass_context
def status(ctx):
    """Summary of tasks (default command)."""
    active = task_client.export(["+ACTIVE"])
    count = _count_mail()
    refspath = expanduser("~/Documents/reference/0sort")

    print(
        f"""
Tasks
  {len(task_client.export(['+OVERDUE'])):3d} overdue
  {len(active):3d} active {" (`ta` for more):" if len(active) else ""}"""
    )
    for _, task in active.iterrows():
        print(f"      {task.id:2d} {task.description}")

    print(
        f"""
{check_output(["timew"], text=True)}
E-mails to process
  {count[0]:3d} inbox
  {count[1]:3d} list traffic

References to sort
  {len(glob(join(refspath, '*.pdf'))) - 2:3d} PDF documents
  {len(glob(join(refspath, '*.bib'))) - 2:3d} BibTeX files
"""
    )

    # Print commands after the status
    formatter = ctx.make_formatter()
    cli.format_commands(ctx, formatter)
    print(formatter.getvalue())


@cli.command()
@click.argument("action", type=click.Choice(["start", "stop"]), default=None, nargs=-1)
def mail(action):
    """Start/stop timewarrior for Inbox 0."""
    # Detect current tracking
    status = check_output(["timew"], text=True)
    current = re.match("Tracking (.*)", status)
    tracking = "Process e-mail" in current[1] if current else False

    try:
        action = action[0]
    except IndexError:
        action = "stop" if tracking else "start"

    if action == "stop" and not tracking:
        # Something wrong
        print(status, end="")
        return

    count = "/".join(map(str, _count_mail()))

    if action == "start":
        check_call(["timew", action, '"Process e-mail"', f"from:{count}"])
    elif action == "stop":
        check_call(["timew", "stop"])
        check_call(["timew", "tag", "@1", f"to:{count}"])
