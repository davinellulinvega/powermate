#!/usr/bin/env python3
import evdev

MAX_BRIGHTNESS = 255
PULSE_SPEED = 255
PULSE_TYPE = 0

ID_VENDOR = 0x077d
ID_PRODUCT = 0x0410


class PowermateLed:
    def __init__(self, max_bright=MAX_BRIGHTNESS, pulse_speed=PULSE_SPEED, pulse_type=PULSE_TYPE):
        self._brightness = max_bright
        self._pulse_speed = pulse_speed
        self._pulse_type = pulse_type

        # Get a handle on the powermate device
        for device_path in evdev.list_devices():
            tmp_device = evdev.InputDevice(device_path)
            tmp_info = tmp_device.info
            if tmp_info.vendor == ID_VENDOR and tmp_info.product == ID_PRODUCT:
                self._device = tmp_device
                break
        else:
            raise RuntimeError("No Powermate device found")

    def pulse(self):
        self._device.write(evdev.ecodes.EV_MSC, evdev.ecodes.MSC_PULSELED, self._brightness | self._pulse_speed << 8 |
                           self._pulse_type << 17 | 1 << 19 | 1 << 20)  # Last to are 'asleep' and 'awake' flags

    def max(self):
        self._device.write(evdev.ecodes.EV_MSC, evdev.ecodes.MSC_PULSELED, self._brightness)

    def off(self):
        self._device.write(evdev.ecodes.EV_MSC, evdev.ecodes.MSC_PULSELED, 0)


    def shutdown(self):
        self.off()
        self._device.close()
