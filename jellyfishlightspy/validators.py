from typing import Tuple, List
from datetime import datetime
from .helpers import JellyFishException
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
    Pattern,
    PortMapping,
    ZoneConfig,
    ScheduleEvent,
    ScheduleEventAction,
)


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

def validate_zone_config(config: ZoneConfig) -> ZoneConfig:
    """Validates zone configurations"""
    if type(config.portMap) is not list or not all(isinstance(pm, PortMapping) for pm in config.portMap):
        raise JellyFishException("ZoneConfig.portMap value is invalid (must be a list of PortMapping objects)")
    for mapping in config.portMap:
        validate_port_mapping(mapping)
    pixel_ct = sum([abs(pm.phyEndIdx - pm.phyStartIdx) + 1 for pm in config.portMap])
    if config.numPixels != pixel_ct:
        raise JellyFishException(f"ZoneConfig.numPixels value {config.numPixels} is invalid (must equal the number of active pixels in the port mapping list: {pixel_ct})")
    #TODO: add check to see if pixel ranges overlap?
    return config

def validate_port_mapping(mapping: PortMapping) -> PortMapping:
    """Validates port mappings in zone configurations"""
    if type(mapping.ctlrName) is not str or mapping.ctlrName == "":
        raise JellyFishException(f"PortMapping.ctlrName value '{mapping.ctlrName}' is invalid (must be a non-empty string)")
    if type(mapping.phyPort) is not int or mapping.phyPort < 1:
        raise JellyFishException(f"PortMapping.phyPort value {mapping.phyPort} is invalid (must be an integer greater than zero)")
    if type(mapping.phyStartIdx) is not int or mapping.phyStartIdx < 0:
        raise JellyFishException(f"PortMapping.phyStartIdx value {mapping.phyStartIdx} is invalid (must be an integer zero or higher)")
    if type(mapping.phyEndIdx) is not int or mapping.phyEndIdx < 0:
        raise JellyFishException(f"PortMapping.phyEndIdx value {mapping.phyEndIdx} is invalid (must be an integer zero or higher)")
    if mapping.zoneRGBStartIdx not in [mapping.phyStartIdx, mapping.phyEndIdx] and mapping.zoneRGBStartIdx != 0:
        raise JellyFishException(f"PortMapping.zoneRGBStartIdx value {mapping.zoneRGBStartIdx} is invalid (must be 0 or equal the phyStartIdx ({mapping.phyStartIdx}) or phyEndIdx ({mapping.phyEndIdx}) value)")
    return mapping

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
    return config

def _date_str_is_valid(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, '%Y%m%d')
        return True
    except ValueError:
        return False

def validate_schedule_event(event: ScheduleEvent, is_calendar_event:bool, valid_patterns: List[str], valid_zones: List[str]) -> ScheduleEvent:
    if type(event.label) is not str:
        raise JellyFishException(f"ScheduleEvent.event value '{event.label}' is invalid (must be a string)")
    if is_calendar_event:
        if not all(len(date_str) == 8 and _date_str_is_valid(date_str) for date_str in event.days):
            raise JellyFishException(f"ScheduleEvent.days value {event.days} is invalid (must be a list of date strings in YYYYMMDD format)")
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
    return action