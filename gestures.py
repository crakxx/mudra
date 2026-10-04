"""Small depth-gesture state machines used by overhead desk mode."""


class DepthTapDetector:
    """Fire once after a finger leaves its learned rest plane and returns."""

    def __init__(self, trigger=0.14, release=0.055, cooldown=0.22,
                 baseline_alpha=0.04):
        if not 0 < release < trigger:
            raise ValueError("release must be smaller than trigger")
        self.trigger = float(trigger)
        self.release = float(release)
        self.cooldown = float(cooldown)
        self.baseline_alpha = float(baseline_alpha)
        self.reset()

    def reset(self):
        self.baseline = None
        self.armed = False
        self.last_fire = float("-inf")

    def update(self, value, now):
        value = float(value)
        now = float(now)
        if self.baseline is None:
            self.baseline = value
            return False

        deviation = abs(value - self.baseline)
        if self.armed:
            if deviation <= self.release:
                self.armed = False
                self.baseline += self.baseline_alpha * (value - self.baseline)
                if now - self.last_fire >= self.cooldown:
                    self.last_fire = now
                    return True
            return False

        if deviation >= self.trigger:
            self.armed = True
            return False

        self.baseline += self.baseline_alpha * (value - self.baseline)
        return False


class DepthHoldDetector:
    """Hold while a finger is lifted away from its learned rest plane."""

    def __init__(self, trigger=0.16, release=0.065, baseline_alpha=0.04):
        if not 0 < release < trigger:
            raise ValueError("release must be smaller than trigger")
        self.trigger = float(trigger)
        self.release = float(release)
        self.baseline_alpha = float(baseline_alpha)
        self.reset()

    def reset(self):
        self.baseline = None
        self.active = False

    def update(self, value):
        value = float(value)
        if self.baseline is None:
            self.baseline = value
            return False, False

        deviation = abs(value - self.baseline)
        changed = False
        if self.active:
            if deviation <= self.release:
                self.active = False
                changed = True
                self.baseline += self.baseline_alpha * (value - self.baseline)
        else:
            if deviation >= self.trigger:
                self.active = True
                changed = True
            else:
                self.baseline += self.baseline_alpha * (value - self.baseline)

        return self.active, changed
