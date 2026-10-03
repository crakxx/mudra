# mudra

**Control your mouse with hand gestures on Linux/Wayland, without giving the app raw keyboard access.**

`mudra` is a webcam air-mouse. MediaPipe hand models run locally through
OpenCV DNN, gestures are converted into pointer actions, and the cursor is
injected through `/dev/uinput` as an absolute virtual tablet.

Global keyboard shortcuts are handled separately by a pinned Electron helper
through the Wayland **XDG GlobalShortcuts portal**. The Python process never
opens physical `/dev/input/event*` keyboard devices.

## Gestures

| Gesture | Action |
|---|---|
| ☝️ point with your **index finger** | move the cursor |
| 🤏 pinch **thumb + middle** | left click; hold to drag |
| 🤙 pinch **thumb + index** | right click |
| ✊ make a **fist** | grab and move; open your hand to drop |

## Hotkeys

When the preview window has focus:

- **P** — pause/resume
- **Q** or **Esc** — quit
- **Ctrl+C** in the launching terminal — quit

Global shortcuts, even when another application has focus:

- **Ctrl+Alt+P** — pause/resume
- **Ctrl+Alt+Q** — quit

On GNOME/Wayland, the desktop normally shows a consent dialog the first time
Mudra requests its global shortcuts. Accepting it persists the bindings for
the installed Mudra desktop identity. KDE Plasma generally exposes the
bindings through System Settings instead of showing the same dialog.

Mudra pins **Electron 45.0.0-alpha.14** exactly. That Electron alpha submits
the shortcuts through the portal, but does not yet expose the portal's final
asynchronous accept/deny result to JavaScript. Mudra therefore treats the
initial registration result only as a submission result and remains usable
with its focused-window shortcuts if global binding is denied.

## Security model

The installer intentionally avoids the broad Linux `input` group.

- Python uses `python-evdev` only to create the virtual `uinput` pointer.
- Python does **not** enumerate or read physical keyboard event devices.
- `/dev/uinput` gets `TAG+="uaccess"`; systemd-logind grants access to the
  active local desktop session instead of permanently granting raw input
  access to the account.
- Electron receives global shortcuts from the desktop portal and sends only
  the allow-listed commands `pause` and `quit` to Python over stdin.
- Python arguments are serialized as JSON rather than interpolated into a
  shell command.
- The two OpenCV ONNX models are pinned to OpenCV Model Zoo commit
  `47534e27c9851bb1128ccc0102f1145e27f23f98` and SHA-256 verified before
  use.
- The Electron package version is exact-pinned and verified after npm install.

If an older Mudra setup previously added your account to the `input` group,
the new setup prints a warning. It does not automatically remove that
membership because another application may rely on it. If Mudra was the only
reason you joined that group, remove it and log out/in:

```bash
sudo gpasswd -d "$USER" input
```

## Requirements

- Linux with Wayland; Ubuntu 26.04/GNOME is a primary target.
- A webcam.
- Python 3 with OpenCV, NumPy, python-evdev and PyQt6.
- Node.js + npm for the pinned Electron launcher.
- systemd-logind/udev `uaccess` support for session-scoped `/dev/uinput`
  access.

`setup.sh` installs distro packages for Debian/Ubuntu, Fedora, Arch and
openSUSE when their supported package managers are available.

## Install

```bash
git clone https://github.com/crakxx/mudra.git
cd mudra
./setup.sh
```

The privileged phase only installs distro packages, loads `uinput`, and
installs the narrow udev rule. Electron, the desktop launcher and the model
files are installed/downloaded as your normal user.

The setup also installs:

- `~/.local/bin/mudra`
- `~/.local/share/applications/io.github.crakxx.mudra.desktop`

That reverse-DNS desktop identity is important on GNOME because the
GlobalShortcuts portal rejects unidentifiable host applications.

## Run

```bash
./run.sh
```

Running `python3 mudra.py` directly is still possible, but global portal
shortcuts are intentionally disabled in that mode.

### Tuning

```bash
./run.sh --pinch 0.7      # easier clicks
./run.sh --margin 0.1     # larger active area / less arm travel
./run.sh --mincutoff 0.7  # steadier cursor, slightly more lag
./run.sh --beta 0.09      # snappier fast movement
./run.sh --median 5       # more smoothing
./run.sh --conf 0.6       # keep tracking harder poses
./run.sh --no-grab        # disable fist-to-grab
```

## Architecture

```text
                         XDG GlobalShortcuts portal
                         ┌─────────────────────────┐
Ctrl+Alt+P / Ctrl+Alt+Q ─▶ Electron 45 alpha      │
                         └───────────┬─────────────┘
                                     │ allow-listed
                                     │ pause / quit
                                     ▼
webcam ─▶ OpenCV DNN ─▶ hand landmarks ─▶ gesture logic
                                     │
                                     ▼
                               /dev/uinput
                                     │
                                     ▼
                             Wayland compositor
```

The camera frames and hand landmarks stay local. There is no runtime network
code in the Python application.

## Model provenance

The downloaded model payloads are verified against the Git LFS SHA-256 object
IDs published by OpenCV Model Zoo:

```text
palm_detection_mediapipe_2023feb.onnx
78ff51c38496b7fc8b8ebdb6cc8c1abb02fa6c38427c6848254cdaba57fcce7c

handpose_estimation_mediapipe_2023feb.onnx
db0898ae717b76b075d9bf563af315b29562e11f8df5027a1ef07b02bef6d81c
```

## Development checks

The lightweight security/syntax checks do not need the models or Electron
runtime:

```bash
./tests/security-smoke.sh
```

## Credits and license

- Hand models: MediaPipe palm detection and hand landmarks from
  [OpenCV Model Zoo](https://github.com/opencv/opencv_zoo), Apache-2.0.
- Original MediaPipe models: Google MediaPipe, Apache-2.0.
- `mp_hand.py` adapts OpenCV Model Zoo pre/post-processing.

Mudra is licensed **AGPL-3.0**; see [LICENSE](LICENSE).
