import json
import time
from typing import Type, Tuple, List, Dict, Any, Optional
from threading import Event
from .model import RunData, PatternData, StateData, Pattern, PortMapping, ZoneData

class JellyFishException(Exception):
    """An exception raised when interacting with the jellyfishlights-py module"""
    pass

class TimelyEvent(Event):
    """
    Event class extended to capture the last time it was set
    """

    def __init__(self):
        Event.__init__(self)
        self.ts: int = 0

    def set(self) -> None:
        """
        Set the internal flag to true and capture the current timestamp (time.perf_counter())

        All threads waiting for it to become true are awakened. Threads
        that call wait() once the flag is true will not block at all. Threads that call wait()
        and set the after_ts argument to a timestamp value before the last set call will not block either.
        """
        self.ts = time.perf_counter()
        Event.set(self)

    def wait(self, timeout: Optional[float] = None, after_ts: Optional[int] = None) -> bool:
        """
        Block until the internal flag is true.

        If the internal flag is true on entry, return immediately. If the after_ts
        argument is set and is greater than the timestamp set at the last set() call,
        return immediately. Otherwise, block until another thread calls set() to
        set the flag to true, or until the optional timeout occurs.

        When the timeout argument is present and not None, it should be a
        floating point number specifying a timeout for the operation in seconds
        (or fractions thereof).

        This method returns the internal flag on exit, so it will always return
        True except if a timeout is given and the operation times out.
        """
        if after_ts and self.ts > after_ts:
            return True
        return Event.wait(self, timeout=timeout)

def validate_intensity(intensity: int) -> int:
    """Validates an individual RGB intensity value (between 0 and 255)"""
    if intensity is None or type(intensity) != int or intensity < 0 or intensity > 255:
        raise JellyFishException(f"RGB intensity value {intensity} is invalid")
    return intensity

def validate_rgb(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Validates an RGB tuple (contains 3 valid intensity values)"""
    if rgb is None or type(rgb) is not tuple or len(rgb) != 3:
        raise JellyFishException(f"RGB value {rgb} is invalid")
    for intensity in rgb:
        validate_intensity(intensity)
    return rgb

def validate_brightness(brightness: int) -> int:
    """Validates a brightness value (between 0 and 100)"""
    if brightness is None or type(brightness) != int or brightness < 0 or brightness > 100:
        raise JellyFishException(f"Brightness value {brightness} is invalid")
    return brightness

def validate_zones(zones: List[str], valid_zones: List[str]) -> List[str]:
    """Validates a list of zone values (must be in the list of values recieved from the controller)"""
    for zone in zones:
        if zone not in valid_zones:
            raise JellyFishException(f"Zone value {zone} is invalid")
    return zones

def validate_pattern(pattern: str, valid_patterns: List[str]) -> str:
    """Validates a pattern value (must be in the list of values recieved from the controller)"""
    if pattern not in [str(p) for p in valid_patterns]:
        raise JellyFishException(f"Pattern value {pattern} is invalid")
    return pattern

def _stringify_state_data(obj):
    """
    Special handling for StateData.data because the API requires an escaped JSON string instead of normal JSON.
    This recursive method searches the input object for StateData dicts and serializes them into a string.
    """
    if type(obj) is list:
        return [_stringify_state_data(value) for value in obj]
    if type(obj) is dict:
        if "data" in obj:
            obj["data"] = json.dumps(obj["data"]) if obj["data"] else ""
        else:
            for k, v in obj.items():
                if type(v) in [list, dict]:
                    obj[k] = _stringify_state_data(v)
    return obj

def to_json(obj: Any) -> str:
    """Serializes Python objects to a JSON string"""
    jstr = json.dumps(obj, default=vars)
    # Convert StateData.data to JSON string instead of plain JSON
    jdict = json.loads(jstr)
    fixed = _stringify_state_data(jdict)
    return json.dumps(fixed)

def _object_hook(data):
    """Determines the object to instantiate based on its attributes"""
    if "speed" in data:
        return RunData(**data)
    if "colors" in data:
        return PatternData(**data)
    if "state" in data:
        if "data" in data and data["data"] != "":
            # Decode StateData.data from escaped JSON string
            data["data"] = json.loads(data["data"], object_hook=_object_hook)
        return StateData(**data)
    if "folders" in data:
        return Pattern(**data)
    if "ctlrName" in data:
        return PortMapping(**data)
    if "numPixels" in data:
        return ZoneData(**data)
    return data

def from_json(json_str: str):
    """Deserializes a JSON string into Python objects"""
    return json.loads(json_str, object_hook=_object_hook)