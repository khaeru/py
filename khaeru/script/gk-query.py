# coding=UTF-8
"""GNOME-Keyring query script

See gk-query for a description.

"""
import curses
import re
import sys

from gi.repository import GnomeKeyring as gk


# keyring to use; if 'None', GnomeKeyring selects the default
KEYRING = None


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
    for item_id in gk.list_item_ids_sync(KEYRING)[1]:
        rc, item = gk.item_get_info_sync(KEYRING, item_id)
        # match the item's name
        if search_re.match(item.get_display_name()):
            found = True
            # prompt the user
            screen.addstr("Display secret for '{}'? [y/N/q] ".format(
                                               item.get_display_name()))
            # single character input
            key = screen.getkey()
            if key in ['y', 'Y']:
                # display the secret
                #commented: the following seems to be broken:
                ## also display the username, if available
                #attrs = gk.Attribute.list_new()
                #gk.item_get_attributes_sync(KEYRING, item_id, attrs)
                #try:
                #    screen.addstr('{}'.format(attrs['username_value']))
                #except KeyError:
                #    pass
                screen.addstr('\n{}\n'.format(item.get_secret()))
            elif key in ['q', 'Q']:
                # quit: push a key to the next getch for a speedy exit
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
        print('{}: gnome-keyring is unavailable'.format(sys.argv[0]))
        sys.exit(1)
    # unlock the login keyring, if necessary
    was_locked = False
    if gk.get_info_sync(KEYRING)[1].get_is_locked():
        was_locked = True
        import getpass
        gk.unlock_sync('login', getpass.getpass(prompt=
          'Enter password for login keyring: '))
    # use curses.wrapper to ensure things are taken care of in case of a
    #   KeyboardInterrupt or other exception
    found = curses.wrapper(query_results, re.compile(r'.*{}.*'.format(
                                                          sys.argv[1])))
    # helpful feedback
    if not found:
        print("No matches for search term '{}'.".format(sys.argv[1]))
    # relock the keyring if necessary
    if was_locked:
        gk.lock_sync(KEYRING)
