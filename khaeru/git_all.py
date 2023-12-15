"""Display information about unclean Git repositories under $HOME.

By default, some repositories are ignored.
"""
import argparse
import os
from pathlib import Path

from colorama import Fore as fg
from git import Repo
from git.exc import GitCommandError

HOME = Path("~").expanduser()

COLORS = {
    "A": fg.RED,
    "M": fg.YELLOW,
    "D": fg.GREEN,
    "R": fg.CYAN,
}

IGNORE = [
    HOME / ".cache",
    HOME / ".local" / "share" / "Trash",
    HOME / "vc" / "other",
]


# Parse simple arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--fetch", action="store_true", help="fetch remotes for comparison (slow)"
)
parser.add_argument(
    "--all",
    dest="verbose",
    action="store_true",
    help="also show information about ignored repos",
)
args = parser.parse_args()


def find_repos():
    for dirpath, dirnames, _ in os.walk(HOME):
        if any(Path(dirpath).is_relative_to(p) for p in IGNORE):
            continue
        if ".git" in dirnames:
            yield Repo(dirpath)


def diff_lines(name, diffs):
    if len(diffs) == 0:
        return

    print(f"  {name}")

    for i, d in enumerate(diffs):
        if i == 0:
            print(COLORS[d.change_type[0]], end="")
        if i < 3:
            print(f"    {d.a_path}")
        else:
            print(f"    … {len(diffs) - 3} more")
            break
    print(fg.RESET, end="")


def plural(num):
    return "{:d} commit{}".format(num, "s" if num > 1 else "")


def main():
    clean = 0

    for repo in find_repos():
        quiet = False  # not args.verbose

        # Optionally fetch remotes
        if args.fetch and not quiet:
            try:
                repo.remotes.origin.fetch()
            except (AttributeError, GitCommandError):
                pass

        # Count number of commits ahead and/or behind upstream
        try:
            ahead_query = "{0}@{{u}}..{0}".format(repo.head.ref)
            behind_query = "{0}..{0}@{{u}}".format(repo.head.ref)
            ahead = sum(1 for c in repo.iter_commits(ahead_query))
            behind = sum(1 for c in repo.iter_commits(behind_query))
        except (TypeError, GitCommandError):
            ahead, behind = 0, 0

        # Get the name of the current branch
        try:
            branch = "on: %s" % repo.active_branch
        except TypeError:
            branch = "detached HEAD"

        # Boolean variables describing repo status
        dirty = repo.is_dirty(untracked_files=True)
        ahead_or_behind = ahead + behind > 0

        if dirty or (ahead_or_behind and not quiet):
            # Identify the repository ahead of other information that may follow
            print("\n~%s (%s)" % (repo.working_dir[len(str(HOME)) :], branch))

            if quiet:
                # A filtered repo, and we're not being verbose
                continue
        else:
            # Not outputting anything about this repository
            clean += 1
            continue

        # Information about commits ahead or behind
        if ahead:
            print(fg.MAGENTA + "  ← %s to push" % plural(ahead) + fg.RESET)
        if behind:
            print(fg.BLUE + "  → %s to fast-forward" % plural(behind) + fg.RESET)

        # Information about the index and working tree
        # Staged
        diff_lines("Staged", repo.index.diff(repo.head.commit))

        # Modified in the working tree
        diff_lines("Working tree", repo.index.diff(None))

        # Untracked files
        untracked = repo.untracked_files
        for i, p in enumerate(repo.untracked_files):
            if i == 0:
                print(fg.GREEN, end="")
            if i < 3:
                print(f"    {p}")
            else:
                print(f"    … {len(untracked) - 3} more")
                break
        print(fg.RESET, end="")

    print("\n%d other clean & synced repositories\n" % clean)
