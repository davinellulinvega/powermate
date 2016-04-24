setup
=====

Create a udev rule by creating the file ```/etc/rules.d/99-powermate.rules```

```ACTION=="add", ENV{ID_USB_DRIVER}=="powermate", SYMLINK+="input/powermate", MODE="0666"
```

After creating the file either restart the udev service or unplug and plug the powermate back in.

requirements
=====

This project requires:
   + pulsectl
   + python-xlib
   + pyautogui
