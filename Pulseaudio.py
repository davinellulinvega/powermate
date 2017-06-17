#!/usr/bin/env python2.7

from pulsectl import Pulse
import notify2 as pynotify


class Pulseaudio():
    """
    Define a simple class interfacing the pulseaudio server with the powermate's actions
    """

    def __init__(self):
        """
        Initialize the connection to the pulseaudio server
        """
        self._pulse = Pulse(threading_lock=True)
        self._note = pynotify.Notification("Volume", "0", "/usr/share/icons/Faenza/apps/48/"
                                                          "gnome-volume-control.png")
        self._note.set_urgency(0)
        pynotify.init("Vol notify")

        # Get the main sink
        for sink in self._pulse.sink_list():
            if sink.card == 1:
                self._main_sink = sink
                break
        else:
            self._main_sink = None

    def get_sinks(self, app_name):
        """
        Get the sink corresponding to the given application
        :param app_name: Name of the application
        :return: None if no corresponding sink is found, PA_SINK object otherwise
        """

        # Initialize the sink
        app_sink = []

        # Make sure the app_name is a string
        if not isinstance(app_name, str) and app_name is not None:
            raise TypeError("Application name should be a String")

        # Get the list of input sinks
        sinks = self._pulse.sink_input_list()
        for sink in sinks:
            # Get the name of the binary associated with the sink
            sink_app_name = sink.proplist.get("application.process.binary", None)
            # Check that the sink is not muted and correspond to the app_name given in parameter
            if sink_app_name is not None and sink_app_name == app_name.lower():
                app_sink.append(sink)

        # Return the sink object
        if len(app_sink) != 0:
            return app_sink
        else:
            return None

    def get_active_sink(self):
        """
        Get the first active pulseaudio sink
        :return: PA_SINK object is any available, None otherwise.
        """

        # Get the list of input sinks
        sinks = self._pulse.sink_input_list()
        for sink in sinks:
            # Check if the sink is muted and attached to an application
            if sink.mute == 0 and sink.proplist.get("application.process.binary", None) is not None:
                return sink

        # If no sink is found return none
        return None

    def short_press(self, app_name=None):
        """
        Toggle the mute state of the sink corresponding to the given app
        :param app_name: The name of the app whose volume should be muted
        :return:
        """

        if app_name is not None:
            # Get the corresponding sink
            sinks = self.get_sinks(app_name)
            # If we got the sink
            if sinks is not None:
                for sink in sinks:
                    # Get the mute state
                    muted = bool(sink.mute)
                    # Toggle the state
                    self._pulse.mute(sink, mute=not muted)

    def rotate_active_sink(self, rotation):
        """
        Increase/decrease the volume of the first active sink
        :param rotation: the direction of the rotation
        :return: Nothing
        """

        # Get the first active sink
        sink = self.get_active_sink()

        # Make sure there is a sink to change
        if sink is not None:
            # Change the volume if possible
            self._pulse.volume_change_all_chans(sink, rotation * 0.005)
            vol = round(self._pulse.volume_get_all_chans(sink) * 100, 1)

            # Display a notification
            self._display_notification(vol)

    def rotate(self, rotation, app_name=None):
        """
        Simply get the list of available sinks
        :param rotation: The direction of rotation. (left = -1, right = 1)
        :param app_name: The name of the active application
        :return:
        """

        if app_name is not None:
            # Get the sink corresponding to the app
            sinks = self.get_sinks(app_name)
            # Initialize a found variable
            found = False
            if sinks is not None:
                for sink in sinks:
                    if sink.mute == 0 and sink is not None:  # The sink was found and is not muted
                        self._pulse.volume_change_all_chans(sink, rotation * 0.005)
                        vol = round(self._pulse.volume_get_all_chans(sink) * 100, 1)

                        # Show the notification
                        self._display_notification(vol)

                        found = True
                if not found:
                    self.rotate_active_sink(rotation)
            else:  # We'll try to change the volume corresponding to clementine media player
                self.rotate_active_sink(rotation)
        else:
            self.rotate_active_sink(rotation)

    def _display_notification(self, volume):
        """
        Display a notification showing the overall current volume.
        :param volume: A float representing the value of the current sink input.
        :return: Nothing.
        """

        # Query the volume of the main sink
        if self._main_sink is not None:
            main_vol = self._main_sink.volume.value_flat
        else:
            main_vol = 1

        # Declare a new notification
        self._note.update("Volume", "{}".format(round(volume * main_vol, 2)), "/usr/share/icons/Faenza/apps/48/"
                                                                              "gnome-volume-control.png")

        # Show the notification
        self._note.show()
