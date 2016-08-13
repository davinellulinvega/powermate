#!/usr/bin/env python2.7

from pulsectl import Pulse
import pynotify


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
            sink_app_name = sink.proplist["application.process.binary"]
            # Check that the sink is not muted and correspond to the app_name given in parameter
            if sink_app_name == app_name.lower():
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
            # Check if the sink is muted or not
            if sink.mute == 0:
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

        # Change the volume if possible
        if sink is not None:
            self._pulse.volume_change_all_chans(sink, rotation * 0.005)
            vol = round(self._pulse.volume_get_all_chans(sink) * 100, 1)
            # Declare a new notification
            self._note.update("Volume", "{}".format(vol), "/usr/share/icons/Faenza/apps/48/"
                                                          "gnome-volume-control.png")

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
                        # Declare a new notification
                        self._note.update("Volume", "{}".format(vol), "/usr/share/icons/Faenza/apps/48/"
                                                                      "gnome-volume-control.png")

                        # Show the notification
                        self._note.show()

                        found = True
                if not found:
                    self.rotate_active_sink(rotation)
            else:  # We'll try to change the volume corresponding to clementine media player
                self.rotate_active_sink(rotation)
