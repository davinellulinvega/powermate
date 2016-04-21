#!/usr/bin/env python3

from __future__ import division

import glob
import powermate
from pulsectl import Pulse


class PowerMate(powermate.PowerMateBase):
    def rotate(self, rotation):
        """
        Simply get the list of available sinks
        :param rotation: The direction of rotation. (left = -1, right = 1)
        :return:
        """

        with Pulse(client_name='volume-increaser', threading_lock=True) as pulse:
            sinks = pulse.sink_input_list()
            for sink in sinks:
                if sink.mute == 0:
                    pulse.volume_change_all_chans(sink, rotation * 0.05)

if __name__ == '__main__':
    try:
        pm = PowerMate(glob.glob('/dev/input/powermate')[0])
        pm.run()
    except KeyboardInterrupt:
        pass
