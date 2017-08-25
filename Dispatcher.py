#!/usr/bin/python3
# -*- coding: utf-8 -*-
import powermate as pm
from Xlib.display import Display
import notify2 as pynotify
from pulsectl import Pulse
import dmenu


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
        self._long_pressed = False
        self._pulse = Pulse(threading_lock=True)
        self._current_sinks = []
        self._display = Display()  # Connects to the default display
        self._note = pynotify.Notification("Volume", "0", "/usr/share/icons/Faenza/apps/48/"
                                                          "gnome-volume-control.png")
        self._note.set_urgency(0)
        pynotify.init("Vol notify")

    def short_press(self):
        """
        Manage the short_press event
        :return: None
        """

        # Check if the long press flag is on
        if self._long_pressed:
            # Toggle the mute state of the current sink
            self._toggle_mute_sinks(self._current_sinks)

        else:
            # Get the class of the active window
            win_cls = self._get_active_win_class()
            if win_cls is not None:
                # Toggle the mute status of the active window
                self._toggle_mute_sinks(self._get_app_sinks(win_cls))

                # Declare a new notification
                self._note.update("Toggle Mute status App.", "{}".format(win_cls), "/usr/share/icons/Faenza/apps/48/gnome-volume-control.png")

                # Show the notification
                self._note.show()

    def long_press(self):
        """
        For the moment this method simply toggles the lights on/off
        :return: A LedEvent class
        """

        if self._long_pressed:
            # Re-initialize the state of the powermate
            self._long_pressed = False
            self._current_sinks = []
            # Just light up the powermate
            return pm.LedEvent.max()
        else:
            # Get the list of active sinks
            sinks = self._get_sinks()
            # Get the names of the apps linked to the sinks
            app_sinks = {sink.proplist.get("application.process.binary") for sink in sinks}
            # Display a menu to select the application to control
            app_name = dmenu.show(list(app_sinks), bottom=True, fast=True, prompt="App. name?", lines=10,
                                  font="Monospace-6:Normal", background_selected="#841313")

            # If successful
            if app_name is not None:
                # Store the list of sinks corresponding to the app name
                self._current_sinks = self._get_app_sinks(app_name)

                # Toggle the long press state
                self._long_pressed = True

                # Have the powermate pulse
                return pm.LedEvent.pulse()

    def rotate(self, rotation):
        """
        Manage the rotate event
        :param rotation: The direction of rotation negative->left, positive->right
        :return: None
        """

        # Check if the long press flag is on
        if self._long_pressed:
            # Change the volume of the current sinks
            self._change_volume_sinks(self._current_sinks, rotation)
        else:
            # Get the class of the active window
            win_cls = self._get_active_win_class()
            if win_cls is not None:
                # Change the volume of the sinks
                self._change_volume_sinks(self._get_app_sinks(win_cls), rotation)

    def _toggle_mute_sinks(self, sinks):
        """
        Simply toggle the mute status of all given sinks.
        :param sinks: A list of sink objects.
        :return: Nothing.
        """

        # Toggle the mute status
        for sink in sinks:
            muted = bool(sink.mute)
            self._pulse.mute(sink, mute=not muted)

    def _change_volume_sinks(self, sinks, rotation):
        """
        Simple change the volume of all given sinks and display a notification.
        :param sinks: A list of sink objects.
        :param rotation: The amount and direction of the rotation.
        :return: Nothing.
        """

        # Change the volume of the sinks
        vol = 0
        for sink in sinks:
            self._pulse.volume_change_all_chans(sink, rotation * 0.005)
            vol = round(self._pulse.volume_get_all_chans(sink) * 100, 1)

        # Show the notification
        self._display_notification(vol)

    def _get_active_win_class(self):
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

    def _get_app_sinks(self, app_name):
        """
        Get the sinks corresponding to the given application
        :param app_name: Name of the application
        :return: List of sink objects otherwise.
        """

        # Make sure the app_name is a string
        if not isinstance(app_name, str) and app_name is not None:
            raise TypeError("Application name should be a String")

        # Get the list of input sinks
        sinks = self._get_sinks()
        # Return the list of sinks corresponding to the application
        return [sink for sink in sinks if sink.proplist.get("application.process.binary").lower() == app_name]

    def _get_sinks(self):
        """
        Get a list of active pulseaudio sinks
        :return: List. A list containing all the active sink objects.
        """

        # Get the list of input sinks
        sinks = [sink for sink in self._pulse.sink_input_list()
                 if sink.proplist.get("application.process.binary", None) is not None]

        # Return the list of active sinks
        return sinks

    def _display_notification(self, volume):
        """
        Display a notification showing the overall current volume.
        :param volume: A float representing the value of the current sink input.
        :return: Nothing.
        """

        # Get the main sink
        for sink in self._pulse.sink_list():
            if sink.card == 1:
                main_vol = sink.volume.value_flat
                break
        else:
            main_vol = 1

        # Declare a new notification
        self._note.update("Volume", "{}".format(round(volume * main_vol, 2)), "/usr/share/icons/Faenza/apps/48/"
                                                                              "gnome-volume-control.png")

        # Show the notification
        self._note.show()

    def _handle_exception(self):
        """
        Close the connection to the pulse server.
        :return: Nothing
        """

        # Close the connection to the pulse server
        self._pulse.close()
        # Try to switch the powermate off
        return pm.LedEvent.off()

if __name__ == "__main__":
    # Create the dispatcher object
    disp = Dispatcher()
    try:
        # Launch it into a new thread
        disp.run()
    except BaseException:
        pass
    finally:
        disp._handle_exception()
