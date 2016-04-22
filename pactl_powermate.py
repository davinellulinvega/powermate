#!/usr/bin/env python3

from __future__ import division

import glob
import powermate
from pulsectl import Pulse


class PowerMate(powermate.PowerMateBase):
    def rotate(self, rotation, app_name=None):
        """
        Simply get the list of available sinks
        :param rotation: The direction of rotation. (left = -1, right = 1)
        :param app_name: The name of the active application
        :return:
        """

        # Make sure the app_name is a string
        if app_name is not isinstance(app_name, str) and app_name is not None:
            raise TypeError("Application name should be a String")

        with Pulse(client_name='volume-increaser', threading_lock=True) as pulse:
            sinks = pulse.sink_input_list()
            for sink in sinks:
                sink_app_name = sink.proplist["application.process.binary"]
                if sink.mute == 0 and sink_app_name == app_name.lower():
                    pulse.volume_change_all_chans(sink, rotation * 0.005)

if __name__ == '__main__':
    try:
        pm = PowerMate(glob.glob('/dev/input/powermate')[0])
        pm.run()
    except KeyboardInterrupt:
        pass
