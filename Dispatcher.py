#!/usr/bin/python
# -*- coding: utf-8 -*-

import powermate as pm
from Pulseaudio import Pulseaudio
from Clementine import Clementine
from Mpv import Mpv
from Xlib.display import Display
import pyautogui

# Declare a global variable for mapping window class to new names
CLS_MAP = {'gl': 'mpv'}


class Dispatcher(pm.PowerMateBase):
    """
    A simple dispatcher class that receive powermate events and dispatch them to the right controller
    """

    def __init__(self, path='/dev/input/powermate'):
        """
        Initialize the super class and define the local members
        :param path: The path to the powermate device
        """
        super(Dispatcher, self).__init__(path, long_threshold=500)
        self._pulsing = False
        self._brightness = pm.MAX_BRIGHTNESS
        self._scroll = False
        self._controllers = {'pulseaudio': Pulseaudio(), 'clementine': Clementine(), 'mpv': Mpv()}
        self._display = Display()  # Connects to the default display

    def short_press(self):
        """
        Manage the short_press event
        :return: None
        """

        # Get the class of the active window
        win_cls = self.get_active_win_class()
        # Dispatch the event to the right controller
        if win_cls is not None and win_cls in self._controllers:
            if hasattr(self._controllers[win_cls], 'short_press'):
                self._controllers[win_cls].short_press()
            else:  # Defaults to the pulseaudio controller
                self._controllers['pulseaudio'].short_press(win_cls)
        else:  # Defaults to the pulseaudio controller
            self._controllers['pulseaudio'].short_press(win_cls)

    def long_press(self):
        """
        For the moment this method simply toggles the lights on/off
        :return: A LedEvent class
        """

        # Get the class of the active window
        win_cls = self.get_active_win_class()
        # Dispatch the event to the right controller
        if win_cls is not None and win_cls in self._controllers:
            if hasattr(self._controllers[win_cls], 'long_press'):
                self._controllers[win_cls].long_press()
            else:
                return pm.LedEvent(speed=pm.MAX_PULSE_SPEED / 2).pulse()
        else:
            # Toggle the scroll state
            self._scroll = not self._scroll
            # Toggle the led's state
            if self._scroll:
                return pm.LedEvent.pulse()
            else:
                return pm.LedEvent.off()

    def rotate(self, rotation):
        """
        Manage the rotate event
        :param rotation: The direction of rotation negative->left, positive->right
        :return: None
        """

        # Check the scroll status
        if self._scroll:
            # Simply scroll up or down
            pyautogui.scroll(rotation * 2)
        else:
            # Get the class of the active window
            win_cls = self.get_active_win_class()
            #print(win_cls)
            # Dispatch the event to the corresponding controller if it exist
            if win_cls is not None and win_cls in self._controllers:
                if hasattr(self._controllers[win_cls], 'rotation'):
                    self._controllers[win_cls].rotate(rotation)
                else:  # Defaults to the pulseaudio controller
                    self._controllers['pulseaudio'].rotate(rotation=rotation, app_name=win_cls)
            else:  # Defaults to the pulseaudio controller
                self._controllers['pulseaudio'].rotate(rotation=rotation, app_name=win_cls)

    def push_rotate(self, rotation):
        """
        For the moment the push rotate will default to previous/next song in the playlist
        :param rotation: The direction of rotation
        :return:
        """

        self._controllers['clementine'].push_rotate(rotation)

    def get_active_win_class(self):
        """
        Use the xlib module to get the class of the window that has the focus
        :return: Return the window class or None if none found
        """

        # Get the window that has the focus
        focus_win = self._display.get_input_focus().focus
        # Get the window class
        win_cls = focus_win.get_wm_class()
        if win_cls is None:
            # Get the class of the parent window
            parent_cls = focus_win.query_tree().parent.get_wm_class()
            if parent_cls is not None:
                return str(parent_cls[-1].lower())
            else:
                return None
        else:
            return str(win_cls[-1].lower())


if __name__ == "__main__":
    try:
        # Create the dispatcher object
        disp = Dispatcher()
        # Launch it into a new thread
        disp.run()
    except KeyboardInterrupt:
        pass
