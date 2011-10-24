# coding=UTF-8
"""GNOME-Keyring query script

See gk-query for a description.

"""
import curses
import re
import sys

import gnomekeyring as gk


def query_results(screen, search_re):
    """Display the query results.

    *screen* is the curses screen set up for this callback function by
    curses.wrapper(). The re.RegexObject *search_re* is matched against the
    display name of every item in the login keyring. For every match found, the
    user is prompted to display the associated secret, skip, or quit.

    Returns True if any items match *search_re*, otherwise False.
    
    """
    curses.use_default_colors()
    # search the login keyring; can't use gk.find_items_sync here because it has
    #   no regex functionality
    found = False
    for item_id in gk.list_item_ids_sync('login'):
        item = gk.item_get_info_sync('login', item_id)
        # match the item's name
        if search_re.match(item.get_display_name()):
            found = True
            # prompt the user
            screen.addstr("Display secret for '%s'? [y/N/q] " % \
              item.get_display_name())
            # single character input
            key = screen.getkey()
            if key in ['y', 'Y']:
                # display the secret
                screen.addstr('\n' + item.get_secret() + '\n')
            elif key in ['q', 'Q']:
                # quitting; push a key to the next getch for a speedy exit
                curses.ungetch(10)
                break
            else:
                screen.addstr('\n')
    # done; pause or eat the key that was ungetch()'d
    screen.addstr('Press any key to continue ...')
    screen.getch()
    # hide the secrets by clearing the screen
    screen.clear()
    return found


if __name__ == '__main__':
    # check that gnome-keyring is available
    if not gk.is_available():
        print '%s: gnome-keyring is unavailable' % sys.argv[0]
        sys.exit(1)
    # unlock the login keyring, if necessary
    was_locked = False
    if gk.get_info_sync('login').get_is_locked():
        was_locked = True
        import getpass
        gk.unlock_sync('login', getpass.getpass(prompt=
          'Enter password for login keyring: '))
    # use curses.wrapper to ensure things are taken care of in case of a
    #   KeyboardInterrupt or other exception
    found = curses.wrapper(query_results, re.compile(r'.*'+ sys.argv[1] +'.*'))
    # helpful feedback
    if not found:
        print "No matches for search term '%s'." % sys.argv[1]
    # relock the keyring if necessary
    if was_locked:
        gk.lock_sync('login')
