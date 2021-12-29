"""Convert mail from MH to Maildir.

See also offlineimap/2021-12-28.conf in the khaeru/dotfiles repo (private).

The process is roughly:

# Create local temporary folders
$ mkdir -p ~/tmp/mail/{DEST_FOLDER}/cur
$ mkdir -p ~/tmp/mail/{DEST_FOLDER}/new
$ mkdir -p ~/tmp/mail/{DEST_FOLDER}/tmp

# Clear status information
$ rm -rf ~/.offlineimap

# Comment "readonly = True" under "[Repository local]"
# Initial sync of the remote folder to the local
$ offlineimap --dry-run -c vc/dotfiles/offlineimap/2021-12-18.conf

# Import messages from an MH folder to the Maildir
$ python -m khaeru.mh_to_maildir

# Comment "readonly = True" under "[Repository remote]"
# Sync the added messages to the remote
$ offlineimap --dry-dun -c vc/dotfiles/offlineimap/2021-12-18.conf

"""

import os
import re
import socket
import time
from email.utils import parsedate
from hashlib import md5
from itertools import chain
from mailbox import Maildir, MaildirMessage
from pathlib import Path

import click

SRC = Path(
    "~/.local/share/claws-mail/imapcache/box2381.bluehost.com/mail@paul.kishimoto.name"
)
SRC_FOLDER = "INBOX/Sent"

DEST = Path("~/tmp/mail/").expanduser()

DEST_FOLDER = "Bluehost_Import_1"


def add_file(go, path):
    if not go:
        print(f"Would add {path}")
        return

    # Open the mailbox
    md = Maildir(DEST.joinpath(DEST_FOLDER), create=False)

    # Determine the UID for the next message
    uid_re = re.compile(",U=([0-9]+),")
    uid = 1 + max(
        chain([0], map(lambda key: int(uid_re.search(key).groups()[0]), md.keys()))
    )

    print(f"Next UID: {uid}")

    # Determine the time when the message was originally delivered
    msg_bytes = path.read_bytes()
    msg = MaildirMessage(msg_bytes)
    msg_time = time.mktime(parsedate(msg["Date"]))

    # Create a Maildir filename in the format used by OfflineIMAP
    key = (
        f"{int(msg_time)}_0.{os.getpid()}.{socket.gethostname()},U={uid},"
        f"FMD5={md5(DEST_FOLDER.encode()).hexdigest()}:2,S"
    )

    # Complete path
    dest = DEST.joinpath(DEST_FOLDER, "cur", key)
    assert not dest.exists() and dest.parent.exists()

    # Write the file
    print(f"Write {key}")
    dest.write_bytes(msg_bytes)

    # Update the utime
    os.utime(dest, (msg_time, msg_time))


@click.command()
@click.option("--go", is_flag=True)
def main(go):
    paths = sorted(
        filter(
            lambda p: p.is_file() and not (p.name.startswith(".") or p.suffix),
            Path(SRC, SRC_FOLDER).expanduser().glob("*"),
        )
    )

    for path in paths:
        add_file(go, path)

    print(f"{len(paths)} paths")


if __name__ == "__main__":
    main()
