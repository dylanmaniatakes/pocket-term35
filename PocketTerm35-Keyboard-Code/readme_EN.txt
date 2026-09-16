# PocketTerm35 Keyboard and Mouse Controls

The dedicated controls next to the arrow keys now act as a USB mouse:

| Dedicated button | Action |
| --- | --- |
| A | Move right while pressed or held |
| Y | Move left while pressed or held |
| X | Move up while pressed or held |
| B | Move down while pressed or held |
| L | Left mouse button; hold while moving to drag |
| R | Right mouse button; hold while moving to drag |

These mappings work with or without Fn. The arrow keys and the normal typing
keys A, B, X, Y, L, and R keep their existing mappings. The modified controls
are matrix row 0, columns 4-9; ordinary letter keys are on other rows.
Perpendicular directions allow diagonal movement; opposing directions cancel.

In code.py, MOUSE_STEP sets movement per report (default: 4 relative HID units),
and MOUSE_INTERVAL sets the repeat interval (default: 0.01 seconds). Actual
pointer speed also depends on the host's mouse settings and scan timing.
DEBOUNCE_INTERVAL defaults to 0.02 seconds for press and release filtering.

## Updating an Existing Installation

If CIRCUITPY is visible and the supplied libraries are already installed:

1. Back up the current code.py from CIRCUITPY to your computer.
2. Copy this folder's code.py to the root of CIRCUITPY, replacing the old file.
3. Wait for copying to finish, then run `sync` in a terminal on the Pi and wait
   for it to return. Check that the installed file matches the source, for example:

       cmp ~/PocketTerm35-Keyboard-Code/code.py /media/$USER/CIRCUITPY/code.py

   A successful comparison produces no output. Adjust paths if needed.
4. CircuitPython normally reloads code.py automatically. Test the controls below.
   If a reset is needed, safely unmount CIRCUITPY in the file manager first.
   Do not reset or disconnect the controller while writes are pending.

The mouse changes live in code.py. The bundled .uf2 firmware and compiled .mpy
libraries are unchanged; there is no new UF2 image to build for this change.
Copy code.py and lib only; changes.md and tests are for your computer.

If CIRCUITPY is hidden by boot.py, use the recovery/reinstall procedure below.
The nuke step erases the keyboard controller's existing files. It is not needed
for a routine code.py update when CIRCUITPY is already accessible.

## Control Check After Installation

- Tap each dedicated direction, then hold it; movement should repeat and stop
  after release (allowing for the 20 ms debounce filter and scan timing).
- Hold A+X for diagonal movement and A+Y for no horizontal movement.
- Tap L/R for left/right clicks, and hold L while moving to test dragging.
- Repeat with Fn held; press/release Fn during a drag or directional hold.
- Type a, b, x, y, l, and r using the typing keys and check all four arrows.
- Check existing Fn shortcuts, backlight/audio controls, and display wake.

Host-side simulated tests cover matrix scanning and HID call behavior.
On 2026-09-16, the application was installed on the cyberdeck's controller;
startup was observed over USB serial and the user confirmed that typing and
all mouse controls work. Other Fn functions and long-duration reliability have
not been separately verified on the device.

## Host-Side Regression Tests

From this folder, run with desktop Python 3 (no extra packages required):

    python3 -m unittest discover -s tests -v

These tests use simulated GPIO, time, and HID devices, not the compiled .mpy
libraries or a live CircuitPython device.

---

# RP2040 Keyboard Firmware Installation Guide

## (For Raspberry Pi)

### Preparation

1. Copy **PocketTerm35-Keyboard-Code.zip** to the **Desktop** of your Raspberry Pi.
2. Extract the ZIP file.
3. Open the extracted **PocketTerm35-Keyboard-Code** folder.

---

### Installation Steps

#### Step 1. Enter Bootloader Mode

Press and hold the **BOOT** button.

While holding **BOOT**, press and release the **RESET** button.

Release the **BOOT** button.

The **RPI-RP2** USB drive will appear.

---

#### Step 2. Initialize RP2040

Drag **nuke_universal.uf2** onto the **RPI-RP2** drive.

Wait until the **RPI-RP2** drive appears again automatically.

---

#### Step 3. Install CircuitPython

Drag **firmware.uf2** onto the **RPI-RP2** drive.

Wait until the **CIRCUITPY** USB drive appears.

---

#### Step 4. Update Library

Open the **CIRCUITPY** drive.

Drag the **lib** folder from the firmware package into the **CIRCUITPY** drive.

Replace the existing folder if prompted.

---

#### Step 5. Update Application

Drag **code.py** into the **CIRCUITPY** drive.

Replace the existing **code.py** file if prompted.

Wait for copying to finish, run `sync` in the Pi terminal, and wait for it to
return. Compare the installed code.py with the source using `cmp` as shown
above. The initial CircuitPython file may contain only `print("Hello World!")`;
that placeholder does not implement a keyboard and must be replaced.

---

#### Step 6. Verify and Test

CircuitPython normally reloads the application when code.py is saved. Verify
that normal typing and all dedicated mouse controls work.

If a restart is needed, finish the `sync` and file-comparison steps first,
safely unmount CIRCUITPY in the file manager, then press **RESET** once.
Never reset while the file copy or disk writes are still in progress.

---

#### Step 7. Hide the CIRCUITPY Drive (Optional)

If no further code modification is required, drag **boot.py** into the **CIRCUITPY** drive.

Replace the existing **boot.py** file if prompted.

Run `sync` in the Pi terminal and wait for it to finish. Safely unmount
CIRCUITPY in the file manager, then press **RESET** once.

After restarting, the **CIRCUITPY** drive will be hidden automatically.

---

### Notes

* **nuke_universal.uf2** initializes the RP2040 Flash and removes all existing files.
* **firmware.uf2** installs the CircuitPython firmware.
* The **CIRCUITPY** drive is available only before installing the supplied **boot.py**.
* To modify the firmware again later, simply repeat the installation procedure from **Step 1**.

## Recovery Notes

If the controller appears as a USB keyboard/mouse but does nothing, inspect
CIRCUITPY/code.py and the USB serial output. Merely installing firmware.uf2
and lib does not install the keyboard application.

If Linux reports FAT errors or mounts CIRCUITPY read-only, back up the visible
files and repair the filesystem with administrator assistance before the next
update. Stop attempting writes until the filesystem is repaired. A running
application can still work while the host mounts its storage read-only.
