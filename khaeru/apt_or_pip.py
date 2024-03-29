"""Suggest whether to install Python packages using apt, or pip."""

from collections import defaultdict
from functools import lru_cache
from pathlib import Path
import re
import subprocess

import click
from packaging.version import parse
import requests


NO_VERSION = parse("0.0.0")


def apt_name(name: str) -> str:
    """Return a candidate Ubuntu (apt) package name given a PyPI `name`."""
    name = (
        name.replace("sphinxcontrib-", "sphinxcontrib.")
        .replace("py-cpuinfo", "cpuinfo")
        .replace("_", "-")
        .lower()
    )
    return f"python3-{name}"


def apt_cache_policy(name):
    def _from_line(line):
        version_str = line.split(": ", maxsplit=1)[-1].split("-")[0]
        return None if version_str == "(none)" else parse(version_str)

    cmd = ["apt-cache", "policy", apt_name(name)]
    lines = subprocess.check_output(cmd, text=True).split("\n")
    try:
        return _from_line(lines[1]), _from_line(lines[2])
    except IndexError:
        return None, None


@lru_cache()
def pip_list():
    lines = subprocess.check_output(["pip", "list"], text=True).split("\n")
    list_re = re.compile(r"^(?P<name>[\w-]+)\W+(?P<version>[\w\.]+)")
    results = dict()
    for line in lines:
        match = list_re.match(line)
        if not match:
            continue
        results[match.group("name")] = parse(match.group("version"))
    return results


def pip_search(name):
    candidate = None

    # cf. https://github.com/pipxproject/pipx/issues/149#issuecomment-491568667
    response = requests.get(f"https://pypi.org/pypi/{name}/json")
    try:
        versions = sorted(map(parse, response.json()["releases"].keys()))
    except ValueError:
        # simplejson.errors.JSONDecodeError
        candidate = None
    else:
        candidate = versions[-1]

    return pip_list().get(name, None), candidate


@click.command(help=__doc__)
@click.option("-r", "--requirement", type=click.Path(exists=True))
@click.argument("specs", nargs=-1)
def main(requirement, specs):
    if requirement:
        assert len(specs) == 0
        specs = Path(requirement).read_text().split("\n")

    actions = defaultdict(set)

    for spec in specs:
        if spec.startswith("#") or not len(spec):
            continue

        try:
            name, min_version = spec.split(">=")
        except ValueError:
            name, min_version = spec, "0.0.0"

        name = name.strip()

        min_version = parse(min_version)

        apt = apt_cache_policy(name)
        pip = pip_search(name)

        print(
            f"\n{name}",
            f">= {min_version}" if min_version > NO_VERSION else "",
        )

        action = "fail"

        if apt[0] and apt[0] >= min_version:
            action = None
            print(f"  -> apt installed {apt[0]} >= {min_version}")
        elif apt[1] and apt[1] >= min_version:
            # apt version will satisfy
            print(f"  -> apt candidate {apt[1]} >= {min_version}")
            action = "apt_install"
        elif apt == (None, None):
            print(f"     apt no match for {apt_name(name)}")
        else:
            print(f"     apt {apt} < {min_version}")

        if pip[0] and pip[0] >= min_version:
            print(f"  -> pip installed {pip[0]} >= {min_version}")
            action = None
        elif action == "fail" and pip[1] and pip[1] >= min_version:
            print(f"  -> pip candidate {pip[1]} >= {min_version}")
            action = "pip_install"
        elif pip[1] and pip[1] < min_version:
            print(f"     pip candidate {pip[1]} < {min_version}")

        actions[action].add(name)

    apt_cmd = "# apt install \\\n  " + " \\\n  ".join(
        apt_name(n) for n in sorted(actions["apt_install"])
    )

    pip_cmd = "$ pip install --upgrade \\\n  " + " \\\n  ".join(
        sorted(actions["pip_install"])
    )

    no_match = "FAILED to match: " + " ".join(sorted(actions["fail"]))

    no_action = "Already up to date: " + " ".join(sorted(actions[None]))

    print(
        "\nShould run:",
        apt_cmd,
        pip_cmd,
        no_match,
        no_action,
        sep="\n\n",
    )
