"""Automate some steps of a Python package release.

See e.g. https://genno.readthedocs.io/en/latest/releasing.html
"""
import re
from datetime import date
from pathlib import Path

import click
from git import Repo
from packaging.version import Version

PATTERN = """Next release
============
"""

REPL = """.. Next release
.. ============

{version} ({date})
{line}
"""


@click.command("prep-release", help=__doc__)
@click.option("--rc", "rc_number", type=int, default=1, help="Release candidate number")
@click.argument("version", type=Version)
def main(version, rc_number):
    # Round-trip through the "Version" type to ensure valid
    v = str(version)
    # With "v" prefix
    vv = f"v{version}"

    repo = Repo(Path.cwd())

    assert not repo.is_dirty(), "Must be in a clean state (no uncommitted changes)"

    # Check not behind origin
    origin = repo.remotes.origin
    origin.fetch()
    assert (
        origin.refs.main.commit == repo.heads.main.commit
    ), "'main' is not in sync with remote 'origin'"

    # Create the new branch and check it out
    head_name = f"release/{v}"
    branch = repo.create_head(head_name, commit=repo.heads.main)
    branch.checkout()

    # Edit doc/whatsnew

    # Path to doc/whatsnew
    p = Path(repo.working_tree_dir).joinpath("doc", "whatsnew.rst")

    # Read the text
    text = p.read_text()

    # Comment the "Next version header", add a new one with the version and date
    _date = date.today().isoformat()
    repl = REPL.format(version=vv, date=_date, line="=" * (3 + len(vv + _date)))
    modified = re.sub(PATTERN, repl, text)
    if modified == text:
        raise click.ClickException(
            "Failed to update doc/whatsnew; please check and retry"
        )

    p.write_text(modified)

    # Stage, commit, and tag
    repo.index.add([p])
    commit = repo.index.commit(f"Mark {vv} in doc/whatsnew")
    tag_name = f"{vv}rc{rc_number}"
    repo.create_tag(tag_name, ref=commit)

    print(
        f"""Next, inspect what was done with:
  git log --oneline && git show HEAD

If necessary, undo with:
  git checkout main && git branch -D {head_name} && git tag -d {tag_name}

or, push and create a pull request:
  git push --tags --set-upstream {origin.name} {head_name} && gh pr create --web
"""
    )
