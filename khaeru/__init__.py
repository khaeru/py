from importlib import import_module
from pathlib import Path

import click

repo_path = Path(__file__).parents[1]
scripts_path = Path(__file__).parent.joinpath("script")


@click.group(help=str(repo_path))
def cli():
    pass


_help = f"""Invoke a script from {repo_path}.

If the first of ARG is a script in {scripts_path}, it is invoked, with the remaining
ARGS passed.
"""


@cli.command(help=_help)
@click.argument("args", nargs=-1)
def run(args):
    from subprocess import run

    args = list(args)

    script_file = scripts_path.joinpath(f"{args.pop(0)}.sh")

    if not script_file.exists():
        raise click.ClickException(f"No script {script_file}\n")

    run([str(script_file)] + args)


@cli.command()
@click.argument("name")
def deps(name):
    """Print dependencies of submodule NAME."""
    from configparser import ConfigParser

    config = ConfigParser()
    config.read(repo_path.joinpath("setup.cfg"))

    try:
        print(config["options.extras_require"][name].strip())
    except KeyError:
        raise click.ClickException(f"No submodule/dependencies for {name}")


for name in ("music.cli", "obsidian.main", "prep_release.main"):
    mod_name, cmd_name = name.rsplit(".", maxsplit=1)
    module = import_module(f"khaeru.{mod_name}")
    cli.add_command(getattr(module, cmd_name))
