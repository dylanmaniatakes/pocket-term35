# Waveshare PocketTerm35

This folder keeps the small, official Waveshare overlay package needed to configure the PocketTerm35 display on a Raspberry Pi. The PocketTerm35 uses a 640×480, 3.5-inch touchscreen and supports Raspberry Pi 4B and 5 variants.

## Files

- [`3.5HDMI_E_DTBO.zip`](3.5HDMI_E_DTBO.zip) — original Waveshare archive, preserved with its upstream filename.
- [`driver-files/3.5HDMI_E_DTBO/`](driver-files/3.5HDMI_E_DTBO/) — extracted upstream files:
  `waveshare-35dpi-3b.dtbo`, `waveshare-35dpi-4b.dtbo`, and `waveshare-35dpi-5b.dtbo`.

For a Raspberry Pi 4B, use `waveshare-35dpi-4b.dtbo`. Do not install the 3B or 5B overlay on a Pi 4B.

## Basic setup

1. Flash Raspberry Pi OS with Raspberry Pi Imager and make a backup before changing the boot files.
2. Copy the matching `.dtbo` file into the SD card's `/boot/overlays/` directory.
3. Add the following to `/boot/config.txt` (or the active boot configuration file used by the image):

   ```ini
   dtparam=i2c_arm=on
   dtoverlay=waveshare-35dpi-4b
   dtoverlay=dwc2,dr_mode=host
   ```

   On a Pi 5, use `dtoverlay=waveshare-35dpi-5b` instead.
4. Boot the Pi, then verify the display and touch input before changing desktop settings.

The overlay is a boot-time hardware description, not a complete desktop driver. Touch orientation, calibration, compositor output selection, and scaling can still require configuration in the active Wayland/X11 stack.

## Authoritative sources

Sources were checked on **2026-09-04**:

- [PocketTerm35 product overview](https://docs.waveshare.com/PocketTerm35)
- [Waveshare software configuration](https://docs.waveshare.com/PocketTerm35/Software-Guide)
- [Waveshare assembly guide](https://docs.waveshare.com/PocketTerm35/Assembly-Guide)
- [Waveshare resources and documents](https://docs.waveshare.com/PocketTerm35/Resources-And-Documents)
- [Original Waveshare driver archive](https://files.waveshare.com/wiki/common/3.5HDMI_E_DTBO.zip)
- [Raspberry Pi OS documentation](https://www.raspberrypi.com/documentation/computers/os.html)

The downloaded archive's SHA-256 is:

```text
bc184c27a2750fb0bd4c8aa18775134d006d4dd8c1b41cff1695648bff3250ad  3.5HDMI_E_DTBO.zip
```

These files are redistributed unchanged for local reference. Waveshare remains the authoritative source for updates, licensing, and hardware-specific support.
