# Keyboard Changes

## 2026-09-16 - English translation and dedicated mouse controls

### Button behavior

Only the six dedicated controls in matrix row 0, columns 4-9 were remapped:

| Button | Matrix position (zero-based) | New action |
| --- | --- | --- |
| L | Row 0, column 4 | Left mouse button |
| R | Row 0, column 5 | Right mouse button |
| X | Row 0, column 6 | Move up |
| Y | Row 0, column 7 | Move left |
| B | Row 0, column 8 | Move down |
| A | Row 0, column 9 | Move right |

The same mappings apply with either Fn key held. Ordinary keyboard letters and
all four arrow keys retain their previous mappings, including their Fn layer.

Movement starts after the switch passes debounce and repeats while held.
Diagonal movement is supported; opposing directions cancel on that axis.
L/R send mouse-down on press and mouse-up on release, supporting clicks and
dragging without repeated clicks. The previous Fn+L/R blocking click routines
were replaced by these button-state handlers.

### Source and documentation

- Translated all Chinese source comments into English. Corrected comments that
  called a False GPIO output "high" to describe the existing low output;
  the output values themselves were not changed. Clarified that the existing
  Super+L shortcut's effect depends on the host desktop.
- Translated readme_CN.txt into English, retaining the supplied filename.
- Expanded readme_EN.txt with the mouse mappings, installation/update steps,
  adjustable speed, test command, and physical validation checklist.
- Added an English explanation to boot.py; its USB-drive hiding behavior is
  unchanged.
- Assigned distinct negative action codes to the dedicated mouse controls so
  they cannot become keyboard letter reports or collide with the typing keys.
- Replaced the 50 ms blocking delay per held key with independent 20 ms
  press/release debounce for each matrix switch. Removed continuous matrix
  debug prints to avoid slowing held movement.
- Added timed relative movement: MOUSE_STEP defaults to 4 HID units and
  MOUSE_INTERVAL to 10 ms, with a 5 ms pause between scans. Actual report rate
  depends on scan execution; pointer speed also depends on host settings.
- Release mouse buttons before the existing blocking display-off/wake handler.
  Attempt keyboard, mouse, and consumer-control release independently on a
  runtime error before the existing controller reset.
- Added tests/test_keyboard.py for host-side simulated regression checks.

### Validation

- All 14 desktop Python regression tests passed. They exercise the actual
  source functions with simulated GPIO, time, and HID devices: all directions
  in both layers, held repeats, release, diagonals, opposing directions,
  independent clicks, dragging, Fn transitions, switch bounce, independent
  debounce, simultaneous typing/mouse use, an existing Fn shortcut, and cleanup
  around display waiting and injected errors.
- Source comparison against the supplied code confirmed that only row 0,
  columns 4-9 changed in KEY_MAP and FN_MAP. All other 128 map cells match.
- Python syntax compilation and English-text/trailing-whitespace checks passed.
- SHA-256 comparisons confirmed all 10 supplied UF2/MPY files are byte-for-byte
  unchanged. No binaries were rebuilt or translated.
- Mouse API behavior was checked against the official Adafruit HID reference:
  https://docs.circuitpython.org/projects/hid/en/latest/api.html#adafruit_hid.mouse.Mouse
- Not validated on physical PocketTerm35 hardware or a live CircuitPython
  runtime. Electrical scan timing, switch feel, USB enumeration, the supplied
  compiled libraries, and host pointer behavior still require an on-device test.

### Deployment

These are local source changes; no device was flashed. Follow readme_EN.txt to
copy code.py onto CIRCUITPY. Back up the installed code.py first for rollback.
If CIRCUITPY is visible and the bundled libraries are already installed, a
routine code.py update does not require the destructive nuke/reinstall steps.


## 2026-09-16 - On-device installation recovery

- Read-only SSH inspection found that CIRCUITPY/code.py was a 22-byte
  `print("Hello World!")` placeholder, not the modified keyboard application.
  All eight installed Adafruit HID .mpy files matched the supplied package.
- The controller identified itself as CircuitPython 10.0.0-beta.0-dirty on a
  Raspberry Pi Pico. Linux enumerated its keyboard and mouse HID interfaces.
- Backed up the placeholder and boot output under
  `/home/ticnitsi/keyboard-recovery-20260916-111801/` on the cyberdeck.
- Copied the full 18,202-byte code.py to CIRCUITPY, flushed the file and host
  writes, and verified byte-for-byte readback. Captured USB serial startup;
  the application started without a Python error during the observation window.
- The user physically tested and confirmed: "Typing and all mouse controls work."
  This adds actual device validation for typing and the requested mouse actions.
  Other Fn functions and long-duration reliability remain separately unverified.
- No source behavior change or UF2 reflash was needed for this recovery.
- Kernel logs showed earlier interrupted USB writes and an unclean FAT volume.
  During recovery Linux reported an invalid FAT entry and remounted CIRCUITPY
  read-only. The keyboard application runs, but storage still needs repair
  before future updates. Administrator access was unavailable over SSH;
  no filesystem repair, formatting, or additional reset was performed.
- Updated readme_EN.txt to require completed copies, `sync`, source/destination
  comparison, and safe unmount before reset. The previous instructions omitted
  these write-completion checks. The exact cause of the lost application and
  filesystem damage was not conclusively established.

### Filesystem repair completed

- The user unmounted CIRCUITPY and ran `fsck.fat -a -V` with administrator
  privileges. It restored the boot-sector volume label, reclaimed 18 unused
  clusters (18,432 bytes), cleared the dirty bit, and completed verification
  without reporting further errors.
- After the user remounted the drive, SSH inspection confirmed CIRCUITPY is
  mounted read-write. Byte-for-byte comparisons confirmed code.py and all eight
  installed HID libraries still match the package.
- No newer FAT errors appeared in the inspected kernel log. A six-second passive
  serial observation showed the code.py running status and no Python errors.
- This resolves the read-only storage issue noted above. No further source
  changes, firmware flashing, or controller reset were needed.
