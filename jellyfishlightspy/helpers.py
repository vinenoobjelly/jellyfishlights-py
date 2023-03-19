import json
import time
from typing import Type, Tuple, List, Dict, Any, Optional
from threading import Event
from .model import RunConfig, PatternConfig, State, Pattern, PortMapping, ZoneConfig
from .requests import SetPatternConfigRequest

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

    def wait(self, timeout: Optional[float] = None, after_ts: Optional[float] = None) -> bool:
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
        return Event.wait(self, timeout = timeout)

def validate_rgb(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Validates an RGB tuple (contains 3 valid intensity values)"""
    if rgb is not None and type(rgb) is tuple and len(rgb) == 3:
        if all((i is not None and type(i) is int and 0 <= i <= 255) for i in rgb):
            return rgb
    raise JellyFishException(f"RGB value {rgb} is invalid (must be a tuple containing three integers between 0 and 255)")

def validate_brightness(brightness: int) -> int:
    """Validates a brightness value (between 0 and 100)"""
    if brightness is not None and type(brightness) is int and 0 <= brightness <= 100:
        return brightness
    raise JellyFishException(f"Brightness value {brightness} is invalid (but be an integer between 0 and 100)")

def validate_zones(zones: List[str], valid_zones: List[str]) -> List[str]:
    """Validates a list of zone values (must be in the list of values recieved from the controller)"""
    invalid_zones = [zone for zone in zones if zone not in valid_zones]
    if len(invalid_zones) == 0:
        return zones
    raise JellyFishException(f"Zone name(s) {invalid_zones} are invalid")

def validate_patterns(patterns: List[str], valid_patterns: List[str]) -> str:
    """Validates pattern values (must be in the list of values recieved from the controller)"""
    invalid_patterns = [pattern for pattern in patterns if pattern not in valid_patterns]
    if len(invalid_patterns) == 0:
        return patterns
    raise JellyFishException(f"Pattern name(s) {invalid_patterns} are invalid")

def _serialize_data_attributes(obj: dict) -> dict:
    """
    Special handling for State.data and SetPatternConfigRequest.patternFileData.jsonData
    because the API requires an escaped JSON string instead of normal JSON
    """
    obj = obj.copy()
    # Encode objects into strings where the API requires it
    for attr in ["data", "jsonData"]:
        if attr in obj:
            obj[attr] = json.dumps(obj[attr], default = _default) if obj[attr] else ""
    # Cover cases where these attributes are on a child dict (e.g. SetPatternConfigRequest)
    for subattr in list(obj):
        if isinstance(obj[subattr], dict):
            obj[subattr] = _serialize_data_attributes(obj[subattr])
    return obj

__ENCODER = json.JSONEncoder()

def _default(obj):
    """Serializes Python objects into dictionaries containing the object's instance variables (via the standard vars() function)."""
    try:
        return _serialize_data_attributes(vars(obj))
    except TypeError:
        pass
    return __ENCODER.default(obj)

def to_json(obj: Any) -> str:
    """Serializes Python objects from this module to a JSON string compatible with the API"""
    return json.dumps(obj, default = _default)

def _object_hook(data):
    """Determines the object to instantiate based on its attributes"""

    # Decode escaped JSON strings that may exist within the plain JSON
    for attr in ["data", "jsonData"]:
        if (attr in data and data[attr] != ""):
            data[attr] = json.loads(data[attr], object_hook = _object_hook)

    # Instantiate the appropriate objects (vs. plain dicts)
    if "speed" in data:
        return RunConfig(**data)
    if "colors" in data:
        return PatternConfig(**data)
    if "state" in data:
        return State(**data)
    if "readOnly" in data:
        return Pattern(**data)
    if "ctlrName" in data:
        return PortMapping(**data)
    if "numPixels" in data:
        return ZoneConfig(**data)
    return data

def from_json(json_str: str):
    """Deserializes a JSON string from the API into Python objects from this module"""
    return json.loads(json_str, object_hook = _object_hook)