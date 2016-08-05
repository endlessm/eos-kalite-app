#!/usr/bin/python
#
# kalite-app.py: helper script to launch KA Lite
#
# Copyright (C) 2016 Endless Mobile, Inc.
# Authors:
#  Mario Sanchez Prada <mario@endlessm.com>
#  Niv Sardi <xaiki@endlessm.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import socket
import sys
from gi.repository import Gio
from gi.repository import GLib

# Where the KA Lite server will be listening.
KALITE_SERVER_URI='http://localhost:8008'

# We use a custom URI that will be handled by chromium-browser-appmode
# so that chromium-browser gets launched with --class and -app set.
DEFAULT_URI = 'webapp://org.learningequality.KALite@{}'.format(KALITE_SERVER_URI)

# In case there's no handler for the webapp:// scheme available.
FALLBACK_URI = KALITE_SERVER_URI

# Maximum time this script is allowed to be running, in seconds.
MAX_TIMEOUT = 60


def exitWithError(main_loop, message):
    print('Error: {}'.format(message))
    main_loop.quit()
    sys.exit(1)


class KALiteLauncher:
    def __init__(self, mainloop):
        self._main_loop = main_loop
        self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self._proxy = Gio.DBusProxy.new_sync(self._bus, Gio.DBusProxyFlags.NONE,
                                             None,
                                             'org.freedesktop.portal.Desktop',
                                             '/org/freedesktop/portal/desktop',
                                             'org.freedesktop.portal.OpenURI',
                                             None)

        # Whether we are trying the custom URI or falling back to HTTP.
        self._fallback_mode = False

        # Run KALite via socket activation
        self._port = 8008
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connection = self._sock.connect_ex(('127.0.0.1', self._port))

        self._start()

    def _start(self, fallback_mode=False):
        self._result = None
        actual_uri = DEFAULT_URI if not self._fallback_mode else FALLBACK_URI
        result = self._proxy.OpenURI('(ssa{sv})',
                                     '',                          # Parent window ID
                                     actual_uri,                  # URI
                                     GLib.Variant('a{sv}', None)) # Options
        if result is None:
            self._tryAgainOrFail()
            return

        # The OpenURI method returns a handle to a 'request object', which stays
        # alive for the duration of the user interaction related to the method call,
        # so we connect to its Response signal to know when it's all over.
        request_handle = result
        self._bus.signal_subscribe('org.freedesktop.portal.Desktop',
                                   'org.freedesktop.portal.Request',
                                   'Response',
                                   request_handle,
                                   None,
                                   Gio.DBusSignalFlags.NO_MATCH_RULE,
                                   self._responseReceived)

    def _tryAgainOrFail(self):
        if not self._fallback_mode:
            self._fallback_mode = True
            self._start()
            return

        exitWithError(self._main_loop, 'Could not launch KA Lite')

    def _responseReceived(self, connection, sender, path, interface, signal, params):
        if not isinstance(params, GLib.Variant):
            self._tryAgainOrFail()
            return

        # Format string for the Response signal is 'ua{sv}', but we are
        # only interested in the first parameter here (response code).
        #
        # Response code values:
        #  0: Success
        #  1: User cancelled action (e.g. Canceled the App Chooser dialog).
        #  2: Error
        (response_code, results) = params.unpack()
        if response_code != 0 and response_code != 1:
            self._tryAgainOrFail()
            return

        # This is not an error, the user explicitly cancelled the action
        # and we don't want to run in fallback mode here, so exit cleanly.
        if response_code == 1:
            print ('Launch cancelled by the user')

        # All good, quit the mainloop and exit cleanly
        self._main_loop.quit()


if __name__ == '__main__':
    main_loop = GLib.MainLoop()
    GLib.timeout_add_seconds(MAX_TIMEOUT, exitWithError, main_loop, 'Timeout reached')
    KALiteLauncher(main_loop)
    main_loop.run()
    sys.exit(0)
