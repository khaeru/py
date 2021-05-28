#!/bin/sh
# Install alternatives for Python 3 to allow switching between
# 3.4 and 3.5 as the default version.
#
# The slaves included are those for which (on Ubuntu 15.10) the
# *3 executable is symlinked by default to a *3.4 executable.
#
# Many executables in /usr/bin named *3 use a shebang line like
# "#!/usr/bin/python3"; so installing one of the alternatives
# below will automatically change the Python version they use.
#
sudo update-alternatives \
	--install /usr/bin/python3 python3 /usr/bin/python3.5 2 \
	--slave /usr/bin/pydoc3 pydoc3 /usr/bin/pydoc3.5 \
	--slave /usr/bin/pygettext3 pygettext3 /usr/bin/pygettext3.5 \
	--slave /usr/bin/python3m python3m /usr/bin/python3.5m
sudo update-alternatives \
	--install /usr/bin/python3 python3 /usr/bin/python3.4 1 \
	--slave /usr/bin/pydoc3 pydoc3 /usr/bin/pydoc3.4 \
	--slave /usr/bin/pygettext3 pygettext3 /usr/bin/pygettext3.4 \
	--slave /usr/bin/python3m python3m /usr/bin/python3.4m
