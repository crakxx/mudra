"""Pure coordinate and camera-geometry helpers for Mudra."""

import math


def validate_area(area):
    if len(area) != 4:
        raise ValueError("area must contain LEFT TOP RIGHT BOTTOM")
    left, top, right, bottom = map(float, area)
    if not (0.0 <= left < right <= 1.0):
        raise ValueError("--area requires 0 <= LEFT < RIGHT <= 1")
    if not (0.0 <= top < bottom <= 1.0):
        raise ValueError("--area requires 0 <= TOP < BOTTOM <= 1")
    return left, top, right, bottom


def transform_normalized(x, y, rotate=0, mirror_x=False, mirror_y=False):
    """Rotate clockwise, then mirror, a normalized camera coordinate."""
    x, y = float(x), float(y)
    if rotate == 0:
        tx, ty = x, y
    elif rotate == 90:
        tx, ty = 1.0 - y, x
    elif rotate == 180:
        tx, ty = 1.0 - x, 1.0 - y
    elif rotate == 270:
        tx, ty = y, 1.0 - x
    else:
        raise ValueError("rotate must be one of 0, 90, 180, 270")
    if mirror_x:
        tx = 1.0 - tx
    if mirror_y:
        ty = 1.0 - ty
    return tx, ty


def camera_point_to_screen(px, py, frame_w, frame_h, area,
                           rotate=0, mirror_x=False, mirror_y=False):
    """Map a raw camera pixel into normalized screen coordinates."""
    if frame_w <= 0 or frame_h <= 0:
        raise ValueError("frame dimensions must be positive")
    left, top, right, bottom = validate_area(area)
    x, y = transform_normalized(
        float(px) / float(frame_w), float(py) / float(frame_h),
        rotate, mirror_x, mirror_y)
    sx = (x - left) / (right - left)
    sy = (y - top) / (bottom - top)
    return min(1.0, max(0.0, sx)), min(1.0, max(0.0, sy))


def validate_camera_angle(angle_degrees):
    """Validate camera elevation above the desk: 0° front, 90° top-down."""
    angle = float(angle_degrees)
    if not 0.0 <= angle <= 90.0:
        raise ValueError("camera angle must be between 0 and 90 degrees")
    return angle


def oriented_vertical_delta(dx, dy, rotate=0):
    """Return image-vertical pixel delta after applying camera rotation.

    Mirroring is intentionally ignored: it changes presentation/mapping, not the
    physical camera elevation used for desk-normal gesture estimation.
    """
    dx, dy = float(dx), float(dy)
    if rotate == 0:
        return dy
    if rotate == 90:
        return dx
    if rotate == 180:
        return -dy
    if rotate == 270:
        return -dx
    raise ValueError("rotate must be one of 0, 90, 180, 270")


def project_desk_normal(tip, base, hand_scale, camera_angle, rotate=0):
    """Estimate fingertip displacement along the desk normal.

    MediaPipe's relative Z is strongest for a top-down camera, while vertical
    image movement is strongest for a frontal camera.  Blend both components
    according to the camera's elevation above the desk:

      0°  -> use oriented image Y only (frontal)
      90° -> use MediaPipe Z only (top-down)

    The result is normalized by hand size so the existing gesture thresholds
    remain approximately scale-independent.
    """
    angle = math.radians(validate_camera_angle(camera_angle))
    scale = max(float(hand_scale), 1e-3)
    dy = oriented_vertical_delta(
        float(tip[0]) - float(base[0]),
        float(tip[1]) - float(base[1]),
        rotate)
    dz = 0.0
    if len(tip) >= 3 and len(base) >= 3:
        dz = float(tip[2]) - float(base[2])
    return (dy * math.cos(angle) + dz * math.sin(angle)) / scale
