"""Source decoration rotation math; preserves existing SDK error boundaries."""
from .project import ProjectError
from rotation_math import Q30,SINE_QUARTER_Q30

def _integer(value, label):
    if type(value) is not int:
        raise ProjectError(f'Decoration rotation requires integer {label}')
    return value


def sin_cos_q30(yaw_units):
    _integer(yaw_units, 'source yaw')
    if not 0 <= yaw_units <= 4095:
        raise ProjectError('Decoration source yaw must be within 0..4095')
    def sine(angle):
        quadrant, at = divmod(angle % 4096, 1024)
        if quadrant == 0:
            return SINE_QUARTER_Q30[at]
        if quadrant == 1:
            return SINE_QUARTER_Q30[1024 - at]
        if quadrant == 2:
            return -SINE_QUARTER_Q30[at]
        return -SINE_QUARTER_Q30[1024 - at]
    return sine(yaw_units), sine(yaw_units + 1024)


def round_q30(numerator):
    _integer(numerator, 'Q30 numerator')
    rounded = (abs(numerator) + Q30 // 2) // Q30
    return -rounded if numerator < 0 else rounded


def rotate_displacement(dx, dz, yaw_units):
    _integer(dx, 'X displacement')
    _integer(dz, 'Z displacement')
    sine, cosine = sin_cos_q30(yaw_units)
    return round_q30(dx * cosine + dz * sine), round_q30(dz * cosine - dx * sine)
