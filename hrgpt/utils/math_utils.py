def clamp_float(value: float, min_value: float, max_value: float) -> float:
    return min(max_value, max(min_value, value))


def clamp_int(value: int, min_value: int, max_value: int) -> int:
    return min(max_value, max(min_value, value))
