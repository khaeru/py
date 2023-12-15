from copy import deepcopy
from itertools import chain
from pathlib import Path

import click


@click.command("bugwarrior-gen-config")
def main():
    """Generate configuration for bugwarrior."""
    import tomlkit
    from xdg_base_dirs import xdg_config_home

    PATH = xdg_config_home().joinpath("bugwarrior", "bugwarrior.toml")

    with open(PATH.with_suffix(".toml.in")) as f:
        doc = tomlkit.load(f)

    template = {}
    new_section = {}
    remove = set()

    def merge_github(template, section, name):
        types = section.pop("_type")

        # Determine whether to generate multiple sections for issues/PRs, or only one
        for label, query_part in (
            ("issue", f"type:issue assignee:{template['login']}"),
            ("pr", f"type:pr assignee:{template['login']}"),
            ("review", f"type:pr review-requested:{template['login']}"),
        ):
            if label not in types:
                continue

            result = deepcopy(template)
            if label == "review":
                result["description_template"] = (
                    "Review " + result["description_template"]
                )

            section.setdefault("query", "")
            for k, v in section.items():
                if k == "query":
                    result[k] = f"{query_part} {template[k]} {v}"
                else:
                    # Simply overwrite
                    result[k] = v

            yield (f"{name}_{label}", result)

    for k, section in doc.items():
        template_id = section.pop("_use", None)
        if not template_id:
            continue

        new_section.update(
            merge_github(template.setdefault(template_id, doc[template_id]), section, k)
        )
        remove.add(k)

    # Remove template and input sections
    for id_ in chain(template, remove):
        doc.pop(id_)

    # Add new sections to the document
    doc.update(new_section)

    # Add new targets
    doc["general"].setdefault("targets", [])
    doc["general"]["targets"].extend(sorted(new_section))

    with open(PATH, "w") as f:
        tomlkit.dump(doc, f)

    print(f"Wrote {PATH}")
