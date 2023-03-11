from typing import Type, Tuple

class JellyFishLightsException(Exception):
    pass

def valid_intensity(intensity: int) -> bool:
    return intensity is not None and type(intensity) == int and 0 <= intensity <= 255

def valid_rgb(rgb: Tuple[int, int, int]) -> bool:
    if rgb is None or type(rgb) is not tuple or len(rgb) != 3:
        return False
    for intensity in rgb:
        if not valid_intensity(intensity):
            return False
    return True

def valid_brightness(brightness: int) -> bool:
    return brightness is not None and type(brightness) == int and 0 <= brightness <= 100

def wrap_exception(msg: str):
    def decorate(f):
        def applicator(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                raise JellyFishLightsException(msg) from e
        return applicator
    return decorate