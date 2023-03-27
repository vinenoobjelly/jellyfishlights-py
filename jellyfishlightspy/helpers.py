import json
import time
from typing import Type, Any, Optional
from threading import Event
from .requests import SetPatternConfigRequest
from .model import (
    RunConfig,
    PatternConfig,
    ZoneState,
    Pattern,
    PortMapping,
    ZoneConfig,
    FirmwareVersion,
    ScheduleEvent,
    ScheduleEventAction,
)

class JellyFishException(Exception):
    """An exception raised when interacting with the jellyfishlights-py module"""
    pass


class TimelyEvent(Event):
    """
    Event class extended to capture the last time it was set
    """

    def __init__(self):
        Event.__init__(self)
        self.ts: float = 0

    def set(self) -> None:
        """
        Set the internal flag to true and capture the current timestamp (time.perf_counter())

        All threads waiting for it to become true are awakened. Threads
        that call wait() once the flag is true will not block at all. Threads that call wait()
        and set the after_ts argument to a timestamp value before the last set call will not block either.
        """
        self.ts = time.perf_counter()
        Event.set(self)

    def wait(self, timeout: Optional[float]=None, after_ts: Optional[float]=None) -> bool:
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

    def trigger(self) -> None:
        """Sets and immediately clears the event"""
        self.set()
        self.clear()


def _serialize_data_attributes(obj: dict) -> dict:
    """
    Special handling for ZoneState.data and SetPatternConfigRequest.patternFileData.jsonData
    because the API requires an escaped JSON string instead of normal JSON
    """
    obj = obj.copy()
    # Encode objects into strings where the API requires it
    for attr in ["data", "jsonData"]:
        if attr in obj:
            obj[attr] = json.dumps(obj[attr], default=_default) if obj[attr] else ""
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
    return json.dumps(obj, default=_default, separators=(',', ':'))

def _object_hook(data):
    """Determines the object to instantiate based on its attributes"""

    # Decode escaped JSON strings that may exist within the plain JSON
    for attr in ["data", "jsonData"]:
        if (attr in data and data[attr] != ""):
            data[attr]=json.loads(data[attr], object_hook=_object_hook)

    # Instantiate the appropriate objects (vs. plain dicts)
    if "ver" in data:
        return FirmwareVersion(**data)
    if "speed" in data:
        return RunConfig(**data)
    if "colors" in data:
        return PatternConfig(**data)
    if "state" in data:
        return ZoneState(**data)
    if "folders" in data and "jsonData" not in data:
        return Pattern(**data)
    if "phyPort" in data:
        return PortMapping(**data)
    if "numPixels" in data:
        return ZoneConfig(**data)
    if "actions" in data:
        return ScheduleEvent(**data)
    if "startFrom" in data:
        return ScheduleEventAction(**data)
    return data

def from_json(json_str: str):
    """Deserializes a JSON string from the API into Python objects from this module"""
    return json.loads(json_str, object_hook=_object_hook)

def copy(obj: Any) -> Any:
    """Copies any serializable object within this library"""
    #TODO: Pretty inefficient... find a less lazy way
    return from_json(to_json(obj))