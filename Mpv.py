#!/usr/bin/python2.7

import pyautogui

class Mpv:
    """
    Manage powermate events for the mpv player
    """

    def long_press(self):
        """
        Play/pause the mpv player
        """
        
        pyautogui.press('p')
