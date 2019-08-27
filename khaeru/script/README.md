# Shell and Python scripts

Copyright © 2010–2019 Paul Natsuo Kishimoto <mail@paul.kishimoto.name>

Made available under the [GNU General Public License v3.0](http://www.gnu.org/licenses/gpl-3.0.html).

To use these scripts, clone the repository:

    $ git clone git@github.com:khaeru/scripts.git $HOME/vc/scripts

Add the directory to your `~/.profile` or `~/.bash_profile` with a line like:

    export PATH=$HOME/vc/scripts:$PATH

## Summary

### Shell

Most of these use a `#!/bin/sh` line, meaning that, on Ubuntu, they run under `dash`, not `bash`. Read more: [1](https://en.wikipedia.org/wiki/Almquist_shell#dash:_Ubuntu.2C_Debian_and_POSIX_compliance_of_Linux_distributions), [2](https://wiki.ubuntu.com/DashAsBinSh).

- `biogeme.sh`, `biosim.sh` — wrappers for [Biogeme](http://biogeme.epfl.ch).
- `gpg-edit` — like `sudoedit`, but for [GPG](https://www.gnupg.org)-encrypted files.
- `gpg-sqlite` — like `gpg-edit`, but for [SQLite](http://www.sqlite.org) databases.
- `install-gams-api` — install the GAMS APIs.
- `install-latexmk` — install the latest version of Latexmk from CTAN.
- `mailman-scrape`
- `new-machine` — configure a new Ubuntu machine.
- `packages` — generate lists of [apt](https://wiki.debian.org/Apt) and [pip](https://pip.pypa.io) packages.
- `ssh-try HOST1 HOST2` — SSH to the first host that connects successfully.

### Python

- `bib` — Command-line utility for BibTeX databases; moved to https://github.com/khaeru/bib.
- `ceic` — process data exported from the CEIC database.
- `disqus-export`
- `git-all` — locate and describe directories under `$HOME` which are [git](https://git-scm.com)-controlled and have uncommitted changes.
   Use git auto-dispatch: `git all`.
- `imgdupe` — find image files in a set of directories with matching *names* and *appearance*, but possibly different *EXIF metadata* or *size*.
- `kdx` — manage Kindle DX collections according to directory structure.
- `maildupe` — choose duplicate files to save/remove from a Maildir mailbox, for clumsy users of [OfflineIMAP](http://offlineimap.org).
- `pim` — various tools for personal information management, as a [click](https://click.palletsprojects.com) application. See `pim --help`.
- `rclone-push` — upload files using [rclone](https://rclone.org) and a file `.rclone-push.yaml` in the current directory.
- `reas_hdf5.py` — convert the [Regional Emissions inventory in ASia (REAS) v2.1](http://www.nies.go.jp/REAS/) into a [HDF5 file](http://en.wikipedia.org/wiki/Hierarchical_Data_Format#HDF5). **Broken.**
- `strip-replies` — a script for use with the [Claws Mail](http://www.claws-mail.org) [Python plugin](http://www.claws-mail.org/plugin.php?plugin=python) to tidy reply messages by removing signatures and blocks of blank lines.
- `task-dedupe` — snippets to assist with removing duplicate tasks in [Taskwarrior](http://taskwarrior.org).
- `task-notify` — similar to https://github.com/flickerfly/taskwarrior-notifications, but in Python, and also reports active time from Taskwarrior.
- `toggle-md0` — in Ubuntu 15.10, gnome-disk-utility [removed md RAID support](https://git.gnome.org/browse/gnome-disk-utility/commit/?id=820e2d3d325aef3574e207a5df73e7480ed41dda); use this with a .desktop file to have a GUI way of starting/stopping an array.
- `xps13` — tweaks for Ubuntu on an old (~2012) Dell XPS 13. Most of these are no longer needed.

### Mixed

- `gk-query`, `gk-query.py` — query the GNOME Keyring for passphrases associated with a particular search string, from the command-line.
  Works headlessly (i.e. without an active GNOME session).
- `svante_jupyter_job.sh`, `svante_jupyter_setup.sh`, `svante_jupyter_tunnel.sh` — run a [Jupyter kernel gateway](https://jupyter-kernel-gateway.readthedocs.io) using [Slurm](https://slurm.schedmd.com) on the MIT svante cluster.

## `old/`: unused scripts—most of which still work!

- `dreamhost-dns.py` — dynamic DNS cron script for [DreamHost](https://www.dreamhost.com).
- `gedit-rubber` — LaTeX compile script using rubber, for the [gedit](https://wiki.gnome.org/Apps/Gedit) plugin ['External Tools'](https://wiki.gnome.org/Apps/Gedit/Plugins/ExternalTools).
- `h5enum.py` — use [xarray](https://xarray.pydata.org) instead.
- `lp986841` — https://bugs.launchpad.net/ubuntu/+source/acroread/+bug/986841/comments/21.
- `moin-migrate` — merge [MoinMoin](https://moinmo.in) data from multiple installations.
- `mount.sh`, `umount.sh`
- `n-way.bzr`, `n-way.py`, `n-way.unison`
- `nm-state` — retcode 0 or 1 according to whether [`nm-tool`](https://wiki.gnome.org/Projects/NetworkManager) says there is a connection active.
- `pythons.sh`
- `rb-alarm.sh` — play [Rhythmbox](https://wiki.gnome.org/Apps/Rhythmbox) from a cron script.
- `reflib-check`, `reflib-scavenge` — for [Referencer](https://launchpad.net/referencer) .reflib databases.
- `rise-and-shine`, `rise-and-shine.py`, `rise-and-shine.ui` — alarm clock using [Music Player Daemon (MPD)](http://www.musicpd.org).
- `synergy`, `synergy-jp`, `synergy-kd` — extreme laziness using [Synergy](http://synergy-project.org).
- `tomboy2zim` — convert [Tomboy](https://wiki.gnome.org/Apps/Tomboy) XML notes to [Zim](http://zim-wiki.org) markup.
