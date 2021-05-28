#!/usr/bin/env python3
"""GNOME-Keyring query script

See gk-query for a description.

"""
import curses
from re import compile
import sys

import gi


# keyring to use; if 'None', GnomeKeyring selects the default
KEYRING = None


def display_results(screen, items):
    """Display the query results.

    *screen* is the curses screen set up for this callback function by
    curses.wrapper(); *items* is an iterable of Secret.Item.

    """
    curses.use_default_colors()

    for item in items:
        attrs = item.get_attributes()

        # Prompt the user
        screen.addstr("Display secret for '{}'? [y/N/q] "
                      .format(attrs['origin_url']))

        # Single character input
        key = screen.getkey()
        if key in ['y', 'Y']:
            # Also display the username, if available
            try:
                screen.addstr('\nusername: {}'.format(attrs['username_value']))
            except KeyError:
                pass
            # Display the secret
            item.load_secret_sync()
            screen.addstr('\n{}\n\n'.format(item.get_secret().get_text()))
        elif key in ['q', 'Q']:
            # Quit: push a key to the next getch for a speedy exit
            curses.ungetch(10)
            break
        else:
            screen.addstr('\n')

    # Done; pause or eat the key that was ungetch()'d
    screen.addstr('Press any key to continue ...')
    screen.getch()


if __name__ == '__main__':
    gi.require_version('GnomeKeyring', '1.0')
    gi.require_version('Secret', '1')
    from gi.repository import GnomeKeyring as gkr, Secret

    # Unlock the login keyring, if necessary
    was_locked = False
    if gkr.get_info_sync(KEYRING)[1].get_is_locked():
        was_locked = True
        import getpass
        result = gkr.unlock_sync('login',
                                 getpass.getpass(prompt='Enter password for '
                                                 'login keyring: '))
        if result == gkr.Result.IO_ERROR:  # Incorrect password
            sys.exit(1)

    # Connect to libsecret
    service = Secret.Service.get_sync(Secret.ServiceFlags.OPEN_SESSION |
                                      Secret.ServiceFlags.LOAD_COLLECTIONS)
    collections = service.get_collections()

    # Search the default keyring
    items = service.unlock_sync(collections, None)[1][0].get_items()

    # Match the item's name using the search string as a regular expression
    found = [i for i in items if compile(sys.argv[1]).search(i.get_label())]

    if len(found):
        # Prompt the user to display any results. Use curses.wrapper to ensure
        # things are taken care of in case of a KeyboardInterrupt or other
        # exception, and that the screen is wiped afterwards.
        curses.wrapper(display_results, found)
    else:
        # Helpful feedback
        print("No matches for search term '{}'.".format(sys.argv[1]))

    # Relock the keyring if necessary
    if was_locked:
        gkr.lock_sync(KEYRING)
