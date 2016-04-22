#!/usr/bin/env python2.7

from pulsectl import Pulse


class Pulseaudio():
    """
    Define a simple class interfacing the pulseaudio server with the powermate's actions
    """

    def __init__(self):
        """
        Initialize the connection to the pulseaudio server
        """
        self._pulse = Pulse(threading_lock=True)

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
            if sinks is not None:
                for sink in sinks:
                    if sink.mute == 0 and sink is not None:  # The sink was found and is not muted
                        self._pulse.volume_change_all_chans(sink, rotation * 0.005)
            else:  # We'll try to change the volume corresponding to clementine media player
                if app_name != "clementine":
                    self.rotate(rotation, "clementine")
