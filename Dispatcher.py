#!/usr/bin/python3
# -*- coding: utf-8 -*-
from time import sleep
from Powermate import Powermate
from PowermateLed import PowermateLed
from Xlib.display import Display
import notify2 as pynotify
from pulsectl import Pulse
from dynmen.rofi import Rofi
from dynmen.menu import MenuError

POLE_TIME = 10
pynotify.init("Vol notify")


class Dispatcher:
    """
    A simple dispatcher class that receive powermate events and dispatch them to the right controller
    """

    def __init__(self, observer):
        """
        Initialize the super class and define the local members
        :param path: The path to the powermate device
        """
        self._long_pressed = False
        self._stored_app = None
        self._display = Display()  # Connects to the default display
        self._note = pynotify.Notification("Volume", "0", "/usr/share/icons/Faenza/apps/48/"
                                                          "gnome-volume-control.png")
        self._note.set_urgency(0)

        self._led = PowermateLed()
        self._led.max()

        self._rofi = Rofi()
        self._rofi.hide_scrollbar = True
        self._rofi.prompt = "App. name?"

    def turn_led_off(self):
        """
        Simply turns the LED off to indicate an error or that the powermate is not being used.
        :return: Nothing
        """

        # Does what it says on the tin
        self._led.off()

    def short_press(self):
        """
        Manage the short_press event
        :return: None
        """

        # Get the list of active sinks
        sinks = self._get_sinks()
        # Get the names of the apps linked to the sinks
        app_sinks = {"{} {}".format(sink.proplist.get("application.name"), sink.index): sink for sink in sinks}
        if len(app_sinks) > 1:
            # Display a menu to select the application to control
            try:
                res = self._rofi(app_sinks)
            except MenuError:
                return
            app_sink = res.value
        elif len(app_sinks) == 1:
            _, app_sink = app_sinks.popitem()
        else:
            app_sink = None

        # If successful
        if app_sink is not None:
            # Toggle the mute status of the selected sink
            self._toggle_mute_sinks([app_sink])

            # Declare a new notification
            self._note.update("Toggle Mute status", "{}".format(app_sink.proplist.get("application.name")), "/usr/share/icons/Faenza/apps/48/gnome-volume-control.png")

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
            self._stored_app = None
            # Just light up the powermate
            self._led.max()
        else:
            # Get the list of active sinks
            sinks = self._get_sinks()
            # Get the names of the apps linked to the sinks
            app_sinks = {sink.proplist.get("application.name"):sink.proplist.get("application.process.binary") for sink in sinks if sink.proplist.get("application.process.binary") not in self._get_active_win_class()}
            if len(app_sinks) > 1:
                # Display a menu to select the application to control
                try:
                    res = self._rofi(app_sinks)
                except MenuError:
                    return
                app_name = res.value
            elif len(app_sinks) == 1:
                _, app_name = app_sinks.popitem()
            else:
                app_name = None

            # If successful
            if app_name is not None:
                # Store the list of sinks corresponding to the app name
                self._stored_app = app_name

                # Toggle the long press state
                self._long_pressed = True

                # Have the powermate pulse
                self._led.pulse()
            else:
                # Make sure the long press flag is off
                self._long_pressed = False
                # Stop the pulse
                self._led.max()

    def rotate(self, rotation):
        """
        Manage the rotate event
        :param rotation: The direction of rotation negative->left, positive->right
        :return: None
        """

        # Get the class of the active window
        win_cls = self._get_active_win_class()
        if win_cls is not None:
            # Change the volume of the sinks
            self._change_volume_sinks(self._get_app_sinks(win_cls), rotation)

    def push_rotate(self, rotation):
        """
        Changes the volume of the sinks registered by the long_press event, according to the given rotation.
        :param rotation: The direction and amplitude of the rotation. (negative = left, positive = right).
        :return: Nothing.
        """

        # Change the volume of the current sinks
        self._change_volume_sinks(self._get_app_sinks(self._stored_app), rotation)

    def _toggle_mute_sinks(self, sinks):
        """
        Simply toggle the mute status of all given sinks.
        :param sinks: A list of sink objects.
        :return: Nothing.
        """

        # Toggle the mute status
        with Pulse(threading_lock=True) as pulse:
            for sink in sinks:
                muted = bool(sink.mute)
                pulse.mute(sink, mute=not muted)

    def _change_volume_sinks(self, sinks, rotation):
        """
        Simple change the volume of all given sinks and display a notification.
        :param sinks: A list of sink objects.
        :param rotation: The amount and direction of the rotation.
        :return: Nothing.
        """

        # Change the volume of the sinks
        with Pulse(threading_lock=True) as pulse:
            for sink in sinks:
                pulse.volume_change_all_chans(sink, rotation * 0.005)

                # Show the notification
                self._display_notification(sink)


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
        if isinstance(app_name, str) and app_name is not None:
            # Get the list of input sinks
            sinks = self._get_sinks()
            # Return the list of sinks corresponding to the application
            return [sink for sink in sinks if sink.proplist.get("application.process.binary").lower() == app_name]
        else:
            return []

    def _get_sinks(self):
        """
        Get a list of active pulseaudio sinks
        :return: List. A list containing all the active sink objects.
        """

        # Get the list of input sinks
        with Pulse(threading_lock=True) as pulse:
            sinks = [sink for sink in pulse.sink_input_list()
                     if sink.proplist.get("application.process.binary", None) is not None]

        # Return the list of active sinks
        return sinks

    def _display_notification(self, sink_in):
        """
        Display a notification showing the overall current volume.
        :param volume: A float representing the value of the current sink input.
        :return: Nothing.
        """

        with Pulse(threading_lock=True) as pulse:
            # Get the volume of the input sink
            volume = pulse.volume_get_all_chans(sink_in)

            # Get the main sink
            for sink in pulse.sink_list():
                if sink.index == sink_in.sink:
                    main_vol = sink.volume.value_flat
                    break
            else:
                main_vol = 1

        # Declare a new notification
        self._note.update("Volume", "{:.1%}".format(volume * main_vol), "/usr/share/icons/Faenza/apps/48/"
                                                                        "gnome-volume-control.png")

        # Show the notification
        self._note.show()

if __name__ == "__main__":
    while True:
        # Create a powermate observer
        try:
            pm = Powermate()
        except OSError:
            sleep(POLE_TIME)
            continue
        except RuntimeError:
            sleep(POLE_TIME)
            continue

        # Create the dispatcher object
        disp = Dispatcher(pm)
        pm.register('short_press', disp.short_press)
        pm.register('long_press', disp.long_press)
        pm.register('press_rotate', disp.push_rotate)
        pm.register('rotate', disp.rotate)

        # Listen for powermate events
        try:
            pm.listen()
        except KeyboardInterrupt:
            pm.shutdown()
            break
        except OSError:
            sleep(POLE_TIME)
        except RuntimeError:
            sleep(POLE_TIME)
        finally:
            disp.turn_led_off()
