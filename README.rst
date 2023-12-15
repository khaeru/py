``khaeru``: Python miscellany
*****************************

.. image:: https://img.shields.io/pypi/v/khaeru.svg
   :target: https://pypi.org/project/khaeru

Everything that doesn't fit somewhere else.

© 2010–2023 Paul Natsuo Kishimoto <`mail@paul.kishimoto.name <mailto:mail@paul.kishimoto.name>`_>.

Licensed under the GNU General Public License, version 3.0 or later.

Install
=======

From source::

    $ git clone git@github.com:khaeru/py.git $HOME/vc/khaeru
    $ cd $HOME/vc/khaeru
    $ pip install --editable .

From PyPI::

    $ pip install khaeru

The only direct requirement is `click`_.
For some of the submodules, below, there are additional requirements; find and install these with::

    $ khaeru deps NAME

    # Example: pipe to pip directly
    $ khaeru deps git-all | xargs pip install

.. _click: https://click.palletsprojects.com


Contents
========

.. contents::
   :local:
   :backlinks: none

Python submodules
-----------------

``khaeru.biogeme``
   …

``khaeru.pelican_ipython``
   Render IPython snippets in Pelican pages, with the help of the Sphinx extension `IPython.sphinxext <https://ipython.readthedocs.io/en/stable/sphinxext.html>`_.
   See e.g. https://paul.kishimoto.name/2021/01/handling-country-codes/

``khaeru.task``
   Code for working with Taskwarrior.

   ``.notify``
      See ``task-notify``, below.

   ``.slack``
      Compute “slack”: amount of work time before given deadlines, after accounting for planned work.


Python submodules with CLI
--------------------------

In addition to ``khaeru``, the following commands are installed.
Most use `click`_, so have their own ``--help``.

``apt-or-pip``
   Suggest whether to install Python packages using apt, or pip.

``bib``
   Command-line utility for BibTeX databases; moved to https://github.com/khaeru/bib.

``ceic``
   Process data exported from the CEIC database.

``dedupe``
   …

``git-all``
   Locate and describe directories under ``$HOME`` which are `git <https://git-scm.com>`_-controlled and have uncommitted changes.
   Use git auto-dispatch: ``git all``.

``pim``
   Various tools for personal information management, as a `click`_ application.
   See ``pim --help``.

``rclone-push``
   Upload files using `rclone <https://rclone.org>`_ and a file ``.rclone-push.yaml`` in the current directory.

``task-notify``
   Similar to https://github.com/flickerfly/taskwarrior-notifications, but in Python, and also reports active time from Taskwarrior.

``strip-replies``
   A script for use with the `Claws Mail <http://www.claws-mail.org>`_ `Python plugin <http://www.claws-mail.org/plugin.php?plugin=python>`_ to tidy reply messages by removing signatures and blocks of blank lines.


Executable Python submodules
----------------------------

Invoke these directly with ``python -m khaeru.NAME``:

``khaeru.disqus-export``
   …

``khaeru.imgdupe``
   Find image files in a set of directories with matching *names* and *appearance*, but possibly different *EXIF metadata* or *size*.

``khaeru.kdx``
   Manage Kindle DX collections according to directory structure.

``khaeru.maildupe``
   Choose duplicate files to save/remove from a Maildir mailbox, for clumsy users of `OfflineIMAP <http://offlineimap.org>`_.

``khaeru.reas_hdf5``
  Convert the `Regional Emissions inventory in ASia (REAS) v2.1 <http://www.nies.go.jp/REAS/>`_ into a `HDF5 file <http://en.wikipedia.org/wiki/Hierarchical_Data_Format#HDF5>`_. **Broken.**


`khaeru/script/ <khaeru/script/>`_: Shell scripts
-------------------------------------------------

Invoke these using ``khaeru run NAME [ARGS]``, or directly.

Most of these use a ``#!/bin/sh`` line, meaning that, on Ubuntu, they run under ``dash``, not ``bash``.
Read more: `1 <https://en.wikipedia.org/wiki/Almquist_shell#dash:_Ubuntu.2C_Debian_and_POSIX_compliance_of_Linux_distributions>`_,
`2 <https://wiki.ubuntu.com/DashAsBinSh>`_.

``biogeme``, ``biosim``
   Wrappers for `Biogeme <http://biogeme.epfl.ch>`_.

``gpg-edit``
   Like ``sudoedit``, but for `GPG <https://www.gnupg.org>`_-encrypted files.

``gpg-sqlite``
   Like ``gpg-edit``, but for `SQLite <http://www.sqlite.org>`_ databases.

``install-gams-api``
   Install the GAMS APIs.

``install-latexmk``
   Install the latest version of Latexmk from CTAN.

``mailman-scrape``
  …

``new-machine``
   Configure a new Ubuntu machine.

``packages``
   Generate lists of `apt <https://wiki.debian.org/Apt>`_ and `pip <https://pip.pypa.io>`_ packages.

``ssh-try HOST1 HOST2``
   SSH to the first host that connects successfully.

``task-dedupe``
   Snippets to assist with removing duplicate tasks in `Taskwarrior <http://taskwarrior.org>`_.

``toggle-md0``
   In Ubuntu 15.10, gnome-disk-utility `removed md RAID support <https://git.gnome.org/browse/gnome-disk-utility/commit/?id=820e2d3d325aef3574e207a5df73e7480ed41dda>`_; use this with a .desktop file to have a GUI way of starting/stopping an array.

``xps13``
   Tweaks for Ubuntu on an old (~2012) Dell XPS 13. Most of these are no longer needed.

``gk-query``, ``gk-query.py``
   Query the GNOME Keyring for passphrases associated with a particular search string, from the command-line.
   Works headlessly (i.e. without an active GNOME session).

``svante_jupyter_job``, ``svante_jupyter_setup``, ``svante_jupyter_tunnel``
   Run a `Jupyter kernel gateway <https://jupyter-kernel-gateway.readthedocs.io>`_ using `Slurm <https://slurm.schedmd.com>`_ on the MIT svante cluster.


`khaeru/old/ <khaeru/old/>`_: Old scripts
-----------------------------------------

Some of these still work, but no guarantees.
No entry point is provided for these; invoke them directly.

``dreamhost-dns.py``
   Dynamic DNS cron script for `DreamHost <https://www.dreamhost.com>`_.

``gedit-rubber``
   LaTeX compile script using rubber, for the `gedit <https://wiki.gnome.org/Apps/Gedit>`_ plugin `'External Tools' <https://wiki.gnome.org/Apps/Gedit/Plugins/ExternalTools>`_.

``h5enum.py``
   Use `xarray <https://xarray.pydata.org>`_ instead.

``lp986841``
   https://bugs.launchpad.net/ubuntu/+source/acroread/+bug/986841/comments/21.

``moin-migrate``
   Merge `MoinMoin <https://moinmo.in>`_ data from multiple installations.

``mount.sh``, ``umount.sh``
   …

``n-way.bzr``, ``n-way.py``, ``n-way.unison``
   N-way diff.

``nm-state``
   Retcode 0 or 1 according to whether `nm-tool <https://wiki.gnome.org/Projects/NetworkManager>`_ says there is a connection active.

``pythons.sh``
   …

``rb-alarm.sh``
   Play `Rhythmbox <https://wiki.gnome.org/Apps/Rhythmbox>`_ from a cron script.

``reflib-check``, ``reflib-scavenge``
   For `Referencer <https://launchpad.net/referencer>`_ .reflib databases.

``rise-and-shine``, ``rise-and-shine.py``, ``rise-and-shine.ui``
   Alarm clock using `Music Player Daemon (MPD) <http://www.musicpd.org>`_.

``synergy``, ``synergy-jp``, ``synergy-kd``
   Extreme laziness using `Synergy <http://synergy-project.org>`_.

``tomboy2zim``
  Convert `Tomboy <https://wiki.gnome.org/Apps/Tomboy>`_ XML notes to `Zim <http://zim-wiki.org>`_ markup.
