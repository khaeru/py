"""Use the ``.. ipython:`` ReST directive from Sphinx, in Pelican."""
import re
from pathlib import Path

from docutils.parsers.rst import directives
from IPython.sphinxext import ipython_directive

from pelican import signals


class IPythonDirective(ipython_directive.IPythonDirective):
    _config = dict()

    @classmethod
    def store_config_options(cls, pelican):
        """New method to retrieve Pelican settings."""
        config = pelican.settings.setdefault("IPYTHON_DIRECTIVE", dict())
        cls._config = config

        config.setdefault("execlines", ["import numpy as np"])
        config.setdefault("holdcount", True)
        config.setdefault("mplbackend", "agg")
        config.setdefault("promptin", "In [%d]:")
        config.setdefault("promptout", "Out[%d]:")
        config.setdefault("rgxin", re.compile(r"In \[(\d+)\]:\s?(.*)\s*"))
        config.setdefault("rgxout", re.compile(r"Out\[(\d+)\]:\s?(.*)\s*"))
        config.setdefault("savefig_dir", "savefig")
        config.setdefault("warning_is_error", True)

    def get_config_options(self):
        """Override to use Pelican configuration."""
        config = self._config

        # get config variables to set figure output directory
        source_dir = Path(self.state.document.settings._source).parent
        savefig_dir = source_dir / config["savefig_dir"]

        return tuple(
            [str(savefig_dir), str(source_dir)]
            + [
                config.get(key)
                for key in [
                    "rgxin",
                    "rgxout",
                    "promptin",
                    "promptout",
                    "mplbackend",
                    "exec_lines",
                    "hold_count",
                    "warning_is_error",
                ]
            ]
        )


def register():
    signals.initialized.connect(IPythonDirective.store_config_options)
    directives.register_directive("ipython", IPythonDirective)
