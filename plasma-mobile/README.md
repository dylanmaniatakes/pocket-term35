# KDE Plasma and Plasma Mobile on Raspberry Pi OS

This guide records the touch-friendly desktop experiment on a **Raspberry Pi 4B** running **64-bit Raspberry Pi OS**.

## Desktop Plasma vs Plasma Mobile

- **KDE Plasma Desktop** is the general desktop workspace. It is not a prerequisite for this Plasma Mobile setup.
- **Plasma Mobile** is KDE's phone/tablet-oriented shell and applications. It is a separate session/package set, not merely a theme for desktop Plasma. On Raspberry Pi OS, package availability can depend on the Debian/Raspberry Pi OS release.

## Install Plasma Mobile

 APT pulls in the shared Plasma/KWin infrastructure required by the mobile shell as dependencies:

```bash
sudo apt update
sudo apt install plasma-mobile
```

The package should add a Plasma Mobile Wayland session. Verify it:

```bash
ls -l /usr/share/wayland-sessions/
grep -RniE 'Name=.*(Plasma|Mobile)|Exec=' \
  /usr/share/wayland-sessions/*plasma* 2>/dev/null
```

Keep the existing `rpd-labwc` session as the fallback. On the tested Raspberry Pi OS setup, LightDM was switched to Plasma Mobile by changing only its autologin session:

```bash
grep -E '^(user-session|autologin-user|autologin-session)=' \
  /etc/lightdm/lightdm.conf

sudo sed -i \
  's/^autologin-session=rpd-labwc$/autologin-session=plasma-mobile/' \
  /etc/lightdm/lightdm.conf
```

Reboot, then use the Plasma Mobile shell. For a one-time test, choose **Plasma Mobile** from the login session menu instead of changing autologin.

## Default-session guidance

Make the desired session the default through the display manager's session selector or by changing `autologin-session` as shown above. To roll back immediately to the tested Raspberry Pi desktop session:

```bash
sudo sed -i \
  's/^autologin-session=plasma-mobile$/autologin-session=rpd-labwc/' \
  /etc/lightdm/lightdm.conf
sudo reboot
```

Do not remove `labwc` or LightDM until Plasma Mobile has survived a reboot and the PocketTerm35 display and touch input work. If no graphical login appears, use a local TTY with `Ctrl+Alt+F2`, sign in, and restore `rpd-labwc`.

## Keep the on-screen keyboards off

On this PocketTerm35, the on-screen keyboard that kept returning was Plasma Mobile's **Maliit** input method. Editing `kwinrc` once is not enough: Plasma Mobile's environment manager can regenerate the mobile defaults at the next login. The durable fix is a private session wrapper that enforces the hardware-keyboard settings immediately before KWin starts.

The normal Raspberry Pi OS `labwc` session does not need this wrapper, just turn on screen keyboard off in settings or via 'sudo raspi-config'


### 1. Back up the current Plasma Mobile configuration

```bash
mkdir -p ~/.config/plasma-mobile
cp ~/.config/plasma-mobile/kwinrc \
   ~/.config/plasma-mobile/kwinrc.before-osk-disable 2>/dev/null || true
```

### 2. Create a PocketTerm-specific Plasma Mobile launcher

Do not modify `/usr/bin/startplasmamobile`; package updates can replace it. Copy it into your user account:

```bash
mkdir -p ~/.local/bin
cp /usr/bin/startplasmamobile ~/.local/bin/startplasmamobile-pideck
nano ~/.local/bin/startplasmamobile-pideck
```

In the copied file, comment out the automatic settings pass:

```bash
# PiDeck: do not regenerate mobile defaults at every login.
# QT_QPA_PLATFORM=offscreen plasma-mobile-envmanager --apply-settings
```

If the copied file contains `--inputmethod maliit-keyboard`, remove that argument so the final launch command is:

```bash
startplasma-wayland --xwayland
```

Immediately above the `# start the shell` comment, add:

```bash
# Set On-Screen Keyboard to off.
sed -i '/^InputMethod.*maliit.*$/d' \
  "$HOME/.config/plasma-mobile/kwinrc"
sed -i 's/^VirtualKeyboardEnabled.*$/VirtualKeyboardEnabled=false/' \
  "$HOME/.config/plasma-mobile/kwinrc"
```

Save the file and make it executable:

```bash
chmod +x ~/.local/bin/startplasmamobile-pideck
```

### 3. Create a separate session entry

Copy the packaged session file, then edit the copy:

```bash
sudo cp /usr/share/wayland-sessions/plasma-mobile.desktop \
  /usr/share/wayland-sessions/plasma-mobile-pideck.desktop
sudo nano /usr/share/wayland-sessions/plasma-mobile-pideck.desktop
```

Change its name to `Plasma Mobile - PiDeck` and change both `Exec=` and `TryExec=` to the full path of the wrapper. Example:

```ini
Exec=/home/Technogizguy/.local/bin/startplasmamobile-pideck
TryExec=/home/Technogizguy/.local/bin/startplasmamobile-pideck
```

Replace `/home/Technogizguy` with your username.

### 4. Make the custom session the autologin session

```bash
sudo sed -i \
  's/^autologin-session=plasma-mobile$/autologin-session=plasma-mobile-pideck/' \
  /etc/lightdm/lightdm.conf
sudo reboot
```

### 5. Verify after reboot

```bash
grep -nE 'InputMethod|VirtualKeyboard' \
  ~/.config/plasma-mobile/kwinrc
ps aux | grep -E 'startplasma|maliit|onboard|matchbox-keyboard|wvkbd' \
  | grep -v grep
```

The desired result is `VirtualKeyboardEnabled=false`, no forced `InputMethod` entry, `startplasma-wayland --xwayland` without the Maliit argument, and no OSK process. The wrapper repeats this on every session start, so a Plasma Mobile update or settings regeneration cannot silently turn the OSK back on.

### Roll back the OSK workaround

Return to the stock Plasma Mobile session:

```bash
sudo sed -i \
  's/^autologin-session=plasma-mobile-pideck$/autologin-session=plasma-mobile/' \
  /etc/lightdm/lightdm.conf
sudo reboot
```

To return to the Raspberry Pi OS desktop instead, use `rpd-labwc` in place of `plasma-mobile`.


## Display and touch caveats

Install the matching PocketTerm35 overlay from [`../waveshare`](../waveshare/) before diagnosing Plasma. The 640×480 display may need explicit output selection or scaling, and touch coordinates may need rotation/calibration after changing compositor or session. Useful checks are:

```bash
echo "$XDG_SESSION_TYPE"
libinput list-devices
libinput debug-events
```

The overlay describes the hardware; it does not guarantee that every Wayland compositor, X11 session, scaling mode, or touch orientation is correct. Test with the Waveshare configuration first, then adjust the active session. Avoid mixing the PocketTerm35 overlay with generic 3.5-inch `LCD-show` scripts.

## Roll back

If Plasma Mobile is not useful, restore `rpd-labwc` first. To remove the package installed by this guide:

```bash
sudo apt remove --purge plasma-mobile
sudo apt autoremove
```

Review the removal list before confirming. Keep packages that were already part of the original system. Remove only the PocketTerm35 overlay lines from the boot configuration if you also want to restore the original display setup.

## References

- [KDE Plasma on Debian](https://wiki.debian.org/KDE)
- [KDE Plasma Mobile: getting it](https://plasma-mobile.org/get/)
- [Debian package: `plasma-mobile`](https://packages.debian.org/plasma-mobile)
- [Raspberry Pi OS documentation](https://www.raspberrypi.com/documentation/computers/os.html)
- [PocketTerm35 software configuration](https://docs.waveshare.com/PocketTerm35/Software-Guide)

This is a tested-on-Raspberry-Pi-4B, not a claim that every Raspberry Pi OS release exposes identical Plasma Mobile packages or that touch calibration is automatic.
