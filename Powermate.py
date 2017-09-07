#!/usr/bin/env python3
import evdev
from Observable import Observable

MAX_BRIGHTNESS = 255
PULSE_SPEED = 255
PULSE_TYPE = 0
LONGPRESS_DELAY = 0.5  # Seconds

ID_VENDOR = 0x077d
ID_PRODUCT = 0x0410


class Powermate(Observable):
    def __init__(self, max_bright=MAX_BRIGHTNESS, pulse_speed=PULSE_SPEED, pulse_type=PULSE_TYPE, longpress_time=LONGPRESS_DELAY):
        super(Powermate, self).__init__()

        self._brightness = max_bright
        self._pulse_speed = pulse_speed
        self._pulse_type = pulse_type
        self._longpress_delay = longpress_time

        # Get a handle on the powermate device
        for device_path in evdev.list_devices():
            tmp_device = evdev.InputDevice(device_path)
            tmp_info = tmp_device.info
            if tmp_info.vendor == ID_VENDOR and tmp_info.product == ID_PRODUCT:
                self._device = tmp_device
                self._device.grab()  # Make sure this is the only application using the device
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
                if event.code not in evdev.ecodes.SYN:  # Ignore synchronization events
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
                        elif not rotated:  # Released
                            pressed = False
                            if (event.timestamp() - press_start) < self._longpress_delay:
                                event_name = 'short_press'
                            else:
                                event_name = 'long_press'
                            for fn in self._observers[event_name]:
                                fn()
                        else:
                            rotated = False
        except OSError as e:
            self.unregister_all()

    def led_pulse(self):
        self._device.write(evdev.ecodes.EV_MSC, evdev.ecodes.MSC_PULSELED, self._brightness | self._pulse_speed << 8 |
                           self._pulse_type << 17 | 1 << 19 | 1 << 20)  # Last to are 'asleep' and 'awake' flags

    def led_max(self):
        self._device.write(evdev.ecodes.EV_MSC, evdev.ecodes.MSC_PULSELED, self._brightness)

    def led_off(self):
        self._device.write(evdev.ecodes.EV_MSC, evdev.ecodes.MSC_PULSELED, 0)

    def shutdown(self):
        self.unregister_all()
        self.led_off()
        self._device.ungrab()
        self._device.close()
