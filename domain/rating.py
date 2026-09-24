from dataclasses import dataclass

NORMAL_MIN = 0.0
NORMAL_MAX = 10.0
SECRET_VALUE = 11.0
STEP = 0.1

def validate_rating(value: float, is_secret: bool) -> float:
    value = float(value)

    if is_secret:
        if value != SECRET_VALUE:
            raise ValueError("Secret rating must be exactly 11.")
        return value

    if not (NORMAL_MIN <= value <= NORMAL_MAX):
        raise ValueError("Normal rating must be between 0 and 10.")

    rounded = round(value, 1)
    if abs(rounded - value) > 1e-9:
        raise ValueError("Normal rating must use increments of 0.1.")

    return rounded

@dataclass(frozen=True)
class TrackRating:
    track_id: int
    value: float
    is_secret: bool = False

    def __post_init__(self):
        validate_rating(self.value, self.is_secret)
