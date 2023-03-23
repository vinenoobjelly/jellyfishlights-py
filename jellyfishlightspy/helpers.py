import json
import time
from typing import Type, Tuple, List, Dict, Any, Optional
from threading import Event
from .requests import SetPatternConfigRequest
from .const import (
    VALID_TYPES,
    VALID_DIRECTIONS,
    VALID_EFFECTS_BETWEEN_PIXELS,
    VALID_EFFECTS,
    VALID_ACTION_TYPES,
    VALID_START_FROMS,
    VALID_DAYS,
)
from .model import (
    RunConfig,
    PatternConfig,
    ZoneState,
    Pattern,
    PortMapping,
    ZoneConfig,
    ControllerVersion,
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
    raise JellyFishException(f"Zone name(s) {invalid_zones} are invalid (valid values are {valid_zones})")

def validate_patterns(patterns: List[str], valid_patterns: List[str]) -> List[str]:
    """Validates pattern values (must be in the list of values recieved from the controller)"""
    invalid_patterns = [pattern for pattern in patterns if pattern not in valid_patterns]
    if len(invalid_patterns) == 0:
        return patterns
    raise JellyFishException(f"Pattern name(s) {invalid_patterns} are invalid")

def validate_pattern_config(config: PatternConfig, valid_zones: List[str]) -> PatternConfig:
    """Validates pattern configuration values"""
    if type(config.colors) is not list or not all((i is not None and type(i) is int and 0 <= i <= 255) for i in config.colors):
        raise JellyFishException(f"PatternConfig.colors value {config.colors} is invalid (must be a list of integers between 0 and 255)")
    if len(config.colors) % 3 != 0:
        raise JellyFishException(f"PatternConfig.colors value {config.colors} is invalid (length must be a multiple of 3)")
    if type(config.colorPos) is not list or not all(type(i) is int for i in config.colorPos):
        raise JellyFishException(f"PatternConfig.colorPos value {config.colors} is invalid (must be a list of integers)")
    if config.type not in VALID_TYPES:
        raise JellyFishException(f"PatternConfig.type value '{config.type}' is invalid (valid values are {VALID_TYPES})")
    if config.direction and config.direction not in VALID_DIRECTIONS: #TODO: Only used if type is multi-paint. Warning message?
        raise JellyFishException(f"PatternConfig.direction value '{config.direction}' is invalid (valid values are {VALID_DIRECTIONS})")
    if type(config.spaceBetweenPixels) is not int:
        raise JellyFishException(f"PatternConfig.spaceBetweenPixels value '{config.spaceBetweenPixels}' is invalid (must be an integer)")
    if type(config.numOfLeds) is not int: #TODO: Only used if type is Stacker. Warning message?
        raise JellyFishException(f"PatternConfig.numOfLeds value '{config.numOfLeds}' is invalid (must be an integer)")
    if type(config.skip) is not int: #TODO: Only used if type is Chase or Stacker. Warning message?
        raise JellyFishException(f"PatternConfig.skip value '{config.skip}' is invalid (must be an integer)")
    if config.effectBetweenPixels not in VALID_EFFECTS_BETWEEN_PIXELS:
        raise JellyFishException(f"PatternConfig.effectBetweenPixels value '{config.effectBetweenPixels}' is invalid (valid values are {VALID_EFFECTS_BETWEEN_PIXELS})")
    if type(config.cursor) is not int:
        raise JellyFishException(f"PatternConfig.cursor value '{config.cursor}' is invalid (must be an integer)")
    #TODO: config.ledOnPos?
    if config.soffitZone and config.soffitZone not in valid_zones:
        raise JellyFishException(f"PatternConfig.soffitZone value '{config.soffitZone}' is invalid (valid values are {valid_zones}")
    if config.runData:
        validate_run_config(config.runData)
    return config

def validate_run_config(config: RunConfig) -> RunConfig:
    """Validates run configuration values"""
    if type(config.speed) is not int:
        raise JellyFishException(f"RunConfig.speed value '{config.speed}' is invalid (must be an integer)")
    if type(config.brightness) is not int or config.brightness < 0 or config.brightness > 100:
        raise JellyFishException(f"RunConfig.brightness value {config.brightness} is invalid (but be an integer between 0 and 100)")
    if config.effect not in VALID_EFFECTS:
        raise JellyFishException(f"RunConfig.effect value '{config.effect}' is invalid (valid values are {VALID_EFFECTS})")
    if type(config.effectValue) is not int:
        raise JellyFishException(f"RunConfig.effectValue value '{config.effectValue}' is invalid (must be an integer)")
    if type(config.rgbAdj) is not list or len(config.rgbAdj) != 3 or not all((i is not None and type(i) is int and 0 <= i <= 255) for i in config.rgbAdj):
        raise JellyFishException(f"RunConfig.rgbAdj value {config.rgbAdj} is invalid (must be a list of three integers between 0 and 255)")

def validate_schedule_event(event: ScheduleEvent, is_calendar_event:bool, valid_patterns: List[str], valid_zones: List[str]) -> ScheduleEvent:
    if type(event.label) is not str:
        raise JellyFishException(f"ScheduleEvent.event value '{event.label}' is invalid (must be a string)")
    if is_calendar_event:
        if not all(len(date_str) in [4, 8] for date_str in event.days):
            raise JellyFishException(f"ScheduleEvent.days value {event.days} is invalid (must be a list of date strings in YYYYMMDD or MMDD format)")
    elif not all(day in VALID_DAYS for day in event.days):
        raise JellyFishException(f"ScheduleEvent.days value {event.days} is invalid (must be a list containing one or more day values: {VALID_DAYS})")
    if type(event.actions) is not list:
        raise JellyFishException(f"ScheduleEvent.actions value {event.actions} is invalid (must be a list)")
    for action in event.actions:
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    zone_sets = [set(action.zones) for action in event.actions]
    if not all(zone_set == zone_sets[0] for zone_set in zone_sets):
        raise JellyFishException("ScheduleEvent.actions zones are invalid (all zone lists must be equal)")
    return event

def validate_schedule_event_action(action: ScheduleEventAction, valid_patterns: List[str], valid_zones: List[str]) -> ScheduleEventAction:
    if action.type not in VALID_ACTION_TYPES:
        raise JellyFishException(f"ScheduleEventAction.type value '{action.type}' is invalid (valid values are: {VALID_ACTION_TYPES})")
    if action.startFrom not in VALID_START_FROMS:
        raise JellyFishException(f"ScheduleEventAction.startFrom value '{action.startFrom}' is invalid (valid values are: {VALID_START_FROMS})")
    if type(action.hour) is not int or action.hour < 0 or action.hour > 23:
        raise JellyFishException(f"ScheduleEventAction.hour value '{action.hour}' is invalid (must be an integer between 0 and 23)")
    if action.startFrom == "time":
        if type(action.minute) is not int or action.minute < 0 or action.minute > 59:
            raise JellyFishException(f"ScheduleEventAction.minute value '{action.minute}' is invalid (must be an integer between 0 and 59 when startFrom='time')")
    elif type(action.minute) is not int or action.minute < -55 or action.minute > 55 or action.minute % 5 != 0:
        raise JellyFishException(f"ScheduleEventAction.minute value '{action.minute}' is invalid (must be an integer between -55 and 55 and divisible by 5 when startFrom!='time')")
    if action.type == "RUN":
        if type(action.patternFile) is not str or action.patternFile not in valid_patterns:
            raise JellyFishException(f"ScheduleEventAction.patternFile value '{action.patternFile}' is invalid")
    if type(action.zones) is not list or not all(zone in valid_zones for zone in action.zones):
        raise JellyFishException(f"ScheduleEventAction.zones value(s) {action.zones} are invalid (valid zones are: {valid_zones})")

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
    return json.dumps(obj, default=_default)

def _object_hook(data):
    """Determines the object to instantiate based on its attributes"""

    # Decode escaped JSON strings that may exist within the plain JSON
    for attr in ["data", "jsonData"]:
        if (attr in data and data[attr] != ""):
            data[attr]=json.loads(data[attr], object_hook=_object_hook)

    # Instantiate the appropriate objects (vs. plain dicts)
    if "ver" in data:
        return ControllerVersion(**data)
    if "speed" in data:
        return RunConfig(**data)
    if "colors" in data:
        return PatternConfig(**data)
    if "state" in data:
        return ZoneState(**data)
    if "folders" in data and "jsonData" not in data:
        return Pattern(**data)
    if "ctlrName" in data:
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