#!/bin/bash
# One-shot setup for mudra. Run as your regular user:
#     ./setup.sh
# It elevates itself (pkexec/sudo) for system packages + narrowly scoped
# /dev/uinput access, then installs the pinned Electron helper and hand models
# as your user.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# System phase (root). Invoked automatically by the user phase below.
# ---------------------------------------------------------------------------
if [ "${1:-}" = "--system" ]; then
    [ "$(id -u)" -eq 0 ] || { echo "--system must run as root"; exit 1; }

    echo "== Installing system packages =="
    if command -v zypper >/dev/null; then
        zypper --non-interactive install --no-recommends \
            python3 python3-opencv python3-numpy python3-evdev python3-PyQt6 \
            qt6-wayland nodejs npm curl
    elif command -v apt-get >/dev/null; then
        apt-get update
        apt-get install -y --no-install-recommends \
            python3 python3-opencv python3-numpy python3-evdev python3-pyqt6 \
            qt6-wayland nodejs npm curl
    elif command -v dnf >/dev/null; then
        dnf install -y \
            python3 python3-opencv python3-numpy python3-evdev python3-pyqt6 \
            qt6-qtwayland nodejs npm curl
    elif command -v pacman >/dev/null; then
        pacman -S --needed --noconfirm \
            python python-opencv python-numpy python-evdev python-pyqt6 \
            qt6-wayland nodejs npm curl
    else
        echo "!! No supported package manager found (zypper/apt/dnf/pacman)."
        echo "   Install manually: python3, OpenCV python bindings, NumPy,"
        echo "   python-evdev, PyQt6, Qt6 Wayland, Node.js, npm and curl."
        echo "   Continuing with /dev/uinput setup..."
    fi

    echo "== Enabling session-scoped /dev/uinput access =="
    modprobe uinput || true
    echo uinput > /etc/modules-load.d/uinput.conf

    # Do NOT add the user to the broad 'input' group.  uaccess lets logind
    # grant /dev/uinput only to the active local seat user via an ACL.
    cat > /etc/udev/rules.d/69-mudra-uinput.rules <<'EOF'
KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput", TAG+="uaccess", MODE:="0660"
EOF
    udevadm control --reload-rules
    udevadm trigger --action=add --subsystem-match=misc --sysname-match=uinput || true
    udevadm settle || true

    echo "== System setup done. No input-group membership was added. =="
    exit 0
fi

# ---------------------------------------------------------------------------
# User phase.
# ---------------------------------------------------------------------------
if [ "$(id -u)" -eq 0 ]; then
    echo "Run ./setup.sh as your regular user; it elevates itself only for"
    echo "the package/udev phase."
    exit 1
fi

echo "== System setup (asks for your password) =="
if command -v pkexec >/dev/null; then
    pkexec "$DIR/setup.sh" --system
else
    sudo "$DIR/setup.sh" --system
fi

if [ ! -e /dev/uinput ] || [ ! -w /dev/uinput ]; then
    echo "ERROR: /dev/uinput is not writable for this active desktop session."
    echo "The udev uaccess rule was installed, but logind did not grant the ACL."
    echo "Check: getfacl /dev/uinput"
    exit 1
fi

echo "== Installing pinned Electron 45 alpha =="
(
    cd "$DIR"
    npm install --include=dev --no-audit --no-fund --package-lock=false --save=false
)

# A real reverse-DNS .desktop identity is required by GNOME's GlobalShortcuts
# portal for non-sandboxed host applications.
echo "== Installing desktop identity for XDG GlobalShortcuts =="
install -d "$HOME/.local/bin" "$HOME/.local/share/applications"
LAUNCHER="$HOME/.local/bin/mudra"
printf '#!/bin/bash\nexec %q "$@"\n' "$DIR/run.sh" > "$LAUNCHER"
chmod 0755 "$LAUNCHER"

desktop_exec="$LAUNCHER"
desktop_exec="${desktop_exec//\\/\\\\}"
desktop_exec="${desktop_exec//\"/\\\"}"
desktop_exec="${desktop_exec//\`/\\\`}"
desktop_exec="${desktop_exec//\$/\\\$}"

cat > "$HOME/.local/share/applications/io.github.crakxx.mudra.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Mudra
Comment=Control the pointer with hand gestures
Exec="${desktop_exec}"
Terminal=false
Categories=Utility;Accessibility;
StartupNotify=false
EOF

if command -v update-desktop-database >/dev/null; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

ZOO="https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models"
for model in \
    "palm_detection_mediapipe/palm_detection_mediapipe_2023feb.onnx" \
    "handpose_estimation_mediapipe/handpose_estimation_mediapipe_2023feb.onnx"
do
    f="$DIR/$(basename "$model")"
    if [ ! -e "$f" ]; then
        echo "== Downloading $(basename "$model") =="
        curl -fL --retry 3 -o "$f" "$ZOO/$model"
    fi
done

echo "== Done. Launch with ./run.sh =="
