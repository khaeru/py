# A variety of Bash and Python scripts

Copyright © 2010–2015 Paul Natsuo Kishimoto <mail@paul.kishimoto.name>

Made available under the [GNU General Public License v3.0](http://www.gnu.org/licenses/gpl-3.0.html).

To use these scripts, clone the repository:

    $ git clone git@github.com:khaeru/scripts.git $HOME/vc/scripts

Add the directory to your `~/.profile` or `~/.bash_profile` with a line like:

    export PATH=$HOME/vc/scripts:$PATH

## Summary
Excluding personal symlinks:

- `bib.py` — BibTeX bibliography management.
- `ceic` — Process data exported from the CEIC database.
- `clean-tex` — Clean all [rubber](https://launchpad.net/rubber) build files for all LaTeX source files in the current directory.
- `flake8` — Ubuntu 15.10 does not ship an executable with the `python3-flake8` package; useful with the Atom [linter-flake8](https://atom.io/packages/linter-flake8) package.
- `git-all` — Locate directories under `$HOME` which are Git-controlled and have uncommitted changes.
- `gk-query`, `gk-query.py` — query the GNOME Keyring for passphrases associated with a particular search string, from the command-line. Works headlessly (i.e. without an active GNOME session).
- `gpg-edit` — `sudoedit` for [GPG](https://www.gnupg.org)-encrypted files.
- `gpg-sqlite` — `gpg-edit` for [SQLite](http://www.sqlite.org) databases.
- `imgdupe` — Find image files in a set of directories with matching *names* and *appearance*, but possibly different *EXIF metadata* or *size*.
- `kdx` — manage Kindle DX collections according to directory structure.
- `maildupe` — Choose duplicate files to save/remove from a Maildir mailbox, for clumsy users of [OfflineIMAP](http://offlineimap.org).
- `mailman-scrape.sh` — ???
- `matlab` — MATLAB R2015a on Ubuntu produces annoying warnings on horizontal touchpad scrolling; squash these.
- `rb-alarm.sh` — play [Rhythmbox](https://wiki.gnome.org/Apps/Rhythmbox) from a cron script.
- `reas_hdf5.py` — convert the [Regional Emissions inventory in ASia (REAS) v2.1](http://www.nies.go.jp/REAS/) into a [HDF5 file](http://en.wikipedia.org/wiki/Hierarchical_Data_Format#HDF5). **Broken.**
- `task-dedupe` — snippets to assist with removing duplicate tasks in [Taskwarrior](http://taskwarrior.org).
- `task-notify` — shameless lift from  https://github.com/flickerfly/taskwarrior-notifications.
- `toggle-md0` — in Ubuntu 15.10, gnome-disk-utility [removed md RAID support](https://git.gnome.org/browse/gnome-disk-utility/commit/?id=820e2d3d325aef3574e207a5df73e7480ed41dda); use this with a .desktop file to have a GUI way of starting/stopping an array.
- `xps13` — tweaks for Ubuntu on an old (~2012) Dell XPS 13. Most of these are no longer needed.

## `old/`: unused scripts

- `dreamhost-dns.py` — dynamic DNS cron script for [DreamHost](https://www.dreamhost.com).
- `gedit-rubber` — LaTeX compile script using rubber, for the [gedit](https://wiki.gnome.org/Apps/Gedit) plugin ['External Tools'](https://wiki.gnome.org/Apps/Gedit/Plugins/ExternalTools).
- `h5enum.py` — use [xray](http://github.com/xray/xray) instead.
- `lp986841` — https://bugs.launchpad.net/ubuntu/+source/acroread/+bug/986841/comments/21.
- `moin-migrate` — Merge [MoinMoin](https://moinmo.in) data from multiple installations.
- `nm-state` — retcode 0 or 1 according to whether [`nm-tool`](https://wiki.gnome.org/Projects/NetworkManager) says there is a connection active.
- `n-way.bzr`, `n-way.py`, `n-way.unison` — …
- `reflib-check`, `reflib-scavenge` — for [Referencer](https://launchpad.net/referencer) .reflib databases.
- `rise-and-shine`, `rise-and-shine.py`, `rise-and-shine.ui` — alarm clock using [Music Player Daemon (MPD)](http://www.musicpd.org).
- `synergy`, `synergy-jp`, `synergy-kd` — extreme laziness using [Synergy](http://synergy-project.org).
- `tomboy2zim` — Convert [Tomboy](https://wiki.gnome.org/Apps/Tomboy) XML notes to [Zim](http://zim-wiki.org) markup.
