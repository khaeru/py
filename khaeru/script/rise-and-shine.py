#!/usr/bin/env python
from datetime import *
import os
from sys import stdin

from gi.repository import Gtk


class Dialog:
    time_formats = ['%H', '%Ia', '%H:%M', '%I:%M %p', ]

    def __init__(self, default):
        self.default = default
        self.builder = Gtk.Builder()
        # GtkBuilder file should be in the same directory
        ui_file = os.path.abspath(__file__).replace('.py', '.ui')
        self.builder.add_from_file(ui_file)
        self.builder.connect_signals(self)
        self.window = self.builder.get_object('dialog')
        if self.window:
            self.window.connect('destroy', Gtk.main_quit)
        self.on_entry_changed(self.builder.get_object('time_entry'))

    def on_entry_changed(self, entry):
        submit = self.builder.get_object('submit_button')
        verify = self.builder.get_object('verify_label')
        for format in self.time_formats:
            try:
                self.value = datetime.strptime(entry.props.text, format)
                submit.props.label = Gtk.STOCK_OK
                verify.props.label = self.value.strftime('= %X')
                return
            except ValueError:
                continue
        submit.props.label = Gtk.STOCK_CANCEL
        verify.props.label = self.default.strftime('(currently %X)')
        return

    def on_clear(self, button):
        print '#* * * * *'
        Gtk.main_quit()
        return

    def on_submit(self, button):
        if button.props.label == Gtk.STOCK_CANCEL:
            d = self.default
        else:
            d = self.value
        print '%d %d * * *' % (d.minute, d.hour)
        Gtk.main_quit()
        return


if __name__ == '__main__':
    d = Dialog(datetime.strptime(stdin.readline().strip(), '%M %H * * *'))
    d.window.show()
    Gtk.main()

