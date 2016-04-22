#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'davinellulinvega'

import dbus
from sys import exit


class Clementine:
    """
    Defines a class to controll the clementine media player through the dbus
    """

    def __init__(self):
        """
        Initialize the Clementine object
        """

        # Initialize the dbus session
        self._dbus = dbus.SessionBus()
        self._dbus_name = self._dbus.get_unique_name()

        # Create a player object
        self._player = None

        # Create two interfaces
        self._ctrl_iface = None
        self._prop_iface = None

    def short_press(self):
        """
        Toggle the play-pause status of the clementine player
        :return:
        """

        # Initialize the player and control interface
        if self._init_objs():
            # Issue a call to the control interface
            self._ctrl_iface.PlayPause()

    def long_press(self):
        """
        Stops whatever the player is playing
        :return:
        """

        # Initialize the player and control interface
        if self._init_objs():
            # Issue a call to the control interface
            self._ctrl_iface.Stop()

    def _init_objs(self):
        """
        Initialize the player, properties interface and control interface
        :return: Boolean, True: success, False: an error occured
        """

        try:
            # Initialize the objects
            self._player = self._dbus.get_object('org.mpris.MediaPlayer2.clementine', '/org/mpris/MediaPlayer2')
            self._ctrl_iface = dbus.Interface(self._player, dbus_interface='org.mpris.MediaPlayer2.Player')
            self._prop_iface = dbus.Interface(self._player, dbus_interface='org.freedesktop.DBus.Properties')
            # Return True upon success
            return True
        except:
            # Yep something went wrong
            return False
