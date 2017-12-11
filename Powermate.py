#!/usr/bin/env python3
import evdev
from time import time
from Observable import Observable

LONGPRESS_DELAY = 0.5  # Seconds
ID_VENDOR = 0x077d
ID_PRODUCT = 0x0410


class Powermate(Observable):
    def __init__(self, longpress_time=LONGPRESS_DELAY):
        super(Powermate, self).__init__()

        self._longpress_delay = longpress_time

        # Get a handle on the powermate device
        for device_path in evdev.list_devices():
            tmp_device = evdev.InputDevice(device_path)
            tmp_info = tmp_device.info
            if tmp_info.vendor == ID_VENDOR and tmp_info.product == ID_PRODUCT:
                self._device = tmp_device
                break
        else:
            raise RuntimeError("No Powermate device found")

    def listen(self):
        # Initialize the press_start variable
        press_start = 0.
        pressed = False
        rotated = False

        try:
            for event in self._device.read_loop():
                # Skip late inputs -- more than 2 seconds late
                if abs(time() - event.timestamp()) > 2:
                    continue

                if event.type not in [evdev.ecodes.EV_SYN, evdev.ecodes.EV_MSC]:  # Ignore synchronization and led events
                    # Rotate
                    if event.code == evdev.ecodes.REL_DIAL and event.type == evdev.ecodes.EV_REL:
                        if pressed:
                            rotated = True
                            for fn in self._observers['press_rotate']:
                                fn(event.value)
                        else:
                            for fn in self._observers['rotate']:
                                fn(event.value)

                    # Press
                    if event.code == evdev.ecodes.BTN_0 and event.type == evdev.ecodes.EV_KEY:
                        if event.value == 1:  # Pressed
                            press_start = event.timestamp()
                            pressed = True
                        else:  # Released
                            if not rotated:
                                if (event.timestamp() - press_start) < self._longpress_delay:
                                    event_name = 'short_press'
                                else:
                                    event_name = 'long_press'
                                for fn in self._observers[event_name]:
                                    fn()

                            pressed = False
                            rotated = False

        except OSError as e:
            self.unregister_all()

    def shutdown(self):
        self.unregister_all()
        self._device.close()
