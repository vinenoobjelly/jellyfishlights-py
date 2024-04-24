# https://medium.com/@joel.barmettler/how-to-upload-your-python-package-to-pypi-65edc5fe9c56
#TODO: get rid of above once this is done

import websocket
from typing import Dict, List, Tuple, Optional, Any
from threading import Thread
from .const import LOGGER, DEFAULT_TIMEOUT
from .model import TimeConfig, Pattern, RunConfig, PatternConfig, ZoneState, ZoneConfig, FirmwareVersion, ScheduleEvent
from .cache import JellyFishCache
from .monitor import WebSocketMonitor
from .helpers import JellyFishException, to_json
from .requests import (
    GetNameRequest,
    GetHostnameRequest,
    GetFirmwareVersionRequest,
    GetTimeConfigRequest,
    GetZoneConfigRequest,
    GetZoneStateRequest,
    GetPatternListRequest,
    GetPatternConfigRequest,
    GetCalendarScheduleRequest,
    GetDailyScheduleRequest,
    SetControllerNameRequest,
    SetZoneStateRequest,
    SetZoneConfigRequest,
    SetPatternConfigRequest,
    SetCalendarScheduleRequest,
    SetDailyScheduleRequest,
    DeletePatternRequest,
)
from .validators import (
    validate_rgb,
    validate_brightness,
    validate_zones,
    validate_zone_config,
    validate_patterns,
    validate_pattern_config,
    validate_schedule_event,
)

# Silence logging - we do our own
websocket.enableTrace(True, level="FATAL")

class JellyFishController:
    """Main interface that enables retrieving data, saving data, and manipulating the lights"""

    def __init__(self, address: str):
        self.address = address
        self.__cache = JellyFishCache()
        self.__ws: websocket.WebSocketApp
        self.__ws_thread: Thread
        self.__ws_monitor = WebSocketMonitor(address, self.__cache)

    def __repr__(self):
        return self.__class__.__name__ + str({"address": self.address, "connected": self.connected})

    @property
    def connected(self) -> bool:
        """Indicates if the the web socket connection to the controller is established"""
        return self.__ws_monitor.connected

    @property
    def name(self) -> str:
        """The controller's user-defined name (returns cached data if available)"""
        return self.__cache.name_data.get_entry() or self.get_name()

    @property
    def hostname(self) -> str:
        """The controller's hostname (returns cached data if available)"""
        return self.__cache.hostname_data.get_entry() or self.get_hostname()

    @property
    def firmware_version(self) -> FirmwareVersion:
        """The controller's version information (returns cached data if available)"""
        return self.__cache.firmware_version_data.get_entry() or self.get_firmware_version()

    @property
    def time_config(self) -> TimeConfig:
        """The controller's timezone configuration (returns cached data if available)"""
        return self.__cache.time_config_data.get_entry() or self.get_time_config()

    @property
    def zone_configs(self) -> Dict[str, ZoneConfig]:
        """The current zones and their configuration (returns cached data if available)"""
        if self.__cache.zone_config_data.size == 0:
            return self.get_zone_configs()
        return self.__cache.zone_config_data.get_all_entries()

    @property
    def zone_names(self) -> List[str]:
        """The current zone names (returns cached data if available)"""
        return list(self.zone_configs)

    @property
    def pattern_list(self) -> List[Pattern]:
        """The list of preset patterns, including folders (returns cached data if available)"""
        if self.__cache.pattern_list_data.size == 0:
            return self.get_pattern_list()
        return list(self.__cache.pattern_list_data.get_all_entries().values())

    @property
    def pattern_names(self) -> List[str]:
        """The current pattern names, excluding folders (returns cached data if available)"""
        return [str(p) for p in self.pattern_list if not p.is_folder]

    @property
    def pattern_configs(self) -> Dict[str, PatternConfig]:
        """The current pattern configurations, excluding folders (returns cached data if available)"""
        if self.__cache.pattern_config_data.size == 0:
            return self.get_pattern_configs()
        return self.__cache.pattern_config_data.get_all_entries()

    @property
    def zone_states(self) -> Dict[str, ZoneState]:
        """The state of each zone (returns cached data if available)"""
        if self.__cache.zone_state_data.size == 0:
            return self.get_zone_states()
        return self.__cache.zone_state_data.get_all_entries()

    @property
    def calendar_schedule(self) -> List[ScheduleEvent]:
        """The list of events in the calendar-based schedule"""
        if self.__cache.calendar_schedule_data.size == 0:
            return self.get_calendar_schedule()
        return self.__cache.calendar_schedule_data.get_entry()

    @property
    def daily_schedule(self) -> List[ScheduleEvent]:
        """The list of events in the daily schedule"""
        if self.__cache.daily_schedule_data.size == 0:
            return self.get_daily_schedule()
        return self.__cache.daily_schedule_data.get_entry()

    def connect(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> None:
        """Establishes a connection to the JellyFish Lighting controller at the given address and begins listening for messages"""
        try:
            self.__ws = websocket.WebSocketApp(
                f"ws://{self.address}:9000",
                on_open = self.__ws_monitor.on_open,
                on_close = self.__ws_monitor.on_close,
                on_message = self.__ws_monitor.on_message,
                on_error = self.__ws_monitor.on_error
            )
            websocket.setdefaulttimeout(timeout)
            self.__ws_thread = Thread(target=lambda: self.__ws.run_forever(), daemon=True)
            self.__ws_thread.start()
            if not self.__ws_monitor.await_connection(timeout):
                self.__ws.close()
                raise JellyFishException(f"Connection to controller at {self.address} timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Could not connect to controller at {self.address}") from e

    def disconnect(self, timeout: Optional[float]=DEFAULT_TIMEOUT):
        """Disconnects from the JellyFish Lighting controller"""
        try:
            self.__ws.close()
            self.__ws_thread.join(timeout)
            if self.__ws_thread.is_alive():
                raise JellyFishException(f"Attempt to disconnect from controller at {self.address} timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while disconnecting from controller at {self.address}") from e

    def __send(self, data: Any) -> None:
        """Sends data to the controller over the web socket connection"""
        if not self.connected:
            raise JellyFishException("Not connected to controller")
        msg = to_json(data)
        LOGGER.debug("Sending: %s", msg)
        self.__ws.send(msg)

    def get_name(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> str:
        """Retrieves the user-defined name for the controller"""
        try:
            self.__send(GetNameRequest())
            if not self.__cache.name_data.await_update(timeout):
                raise JellyFishException("Request for controller name timed out")
            return self.__cache.name_data.get_entry()
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving controller name") from e

    def get_hostname(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> str:
        """Retrieves the hostname from the controller"""
        try:
            self.__send(GetHostnameRequest())
            if not self.__cache.hostname_data.await_update(timeout):
                raise JellyFishException("Request for controller hostname timed out")
            return self.__cache.hostname_data.get_entry()
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving controller hostname") from e

    def get_firmware_version(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> FirmwareVersion:
        """Retrieves version information from the controller"""
        try:
            self.__send(GetFirmwareVersionRequest())
            if not self.__cache.firmware_version_data.await_update(timeout):
                raise JellyFishException("Request for controller version information timed out")
            return self.__cache.firmware_version_data.get_entry()
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving controller version information") from e

    def get_time_config(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> TimeConfig:
        """Retrieves timezone configuration information from the controller"""
        try:
            self.__send(GetTimeConfigRequest())
            if not self.__cache.time_config_data.await_update(timeout):
                raise JellyFishException("Request for time config information timed out")
            return self.__cache.time_config_data.get_entry()
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving controller version information") from e

    def get_zone_names(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> List[str]:
        """Retrieves the list of current zones from the controller and caches the data"""
        return list(self.get_zone_configs(timeout))

    def get_zone_configs(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> Dict[str, ZoneConfig]:
        """Retrieves the list of current zones and their configuration from the controller and caches the data"""
        try:
            self.__send(GetZoneConfigRequest())
            if not self.__cache.zone_config_data.await_finalization(timeout):
                raise JellyFishException("Request for zone config data timed out")
            return self.__cache.zone_config_data.get_all_entries()
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving zone config data") from e

    def get_pattern_names(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> List[str]:
        """Retrieves the list of current patterns from the controller and caches the data"""
        return [str(p) for p in self.get_pattern_list(timeout) if not p.is_folder]

    def get_pattern_list(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> List[Pattern]:
        """Retrieves the list of preset patterns from the controller and caches the data"""
        try:
            self.__send(GetPatternListRequest())
            if not self.__cache.pattern_list_data.await_finalization(timeout):
                raise JellyFishException("Request for pattern list data timed out")
            return list(self.__cache.pattern_list_data.get_all_entries().values())
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving pattern data") from e

    def get_pattern_config(self, pattern: str, timeout: Optional[float]=DEFAULT_TIMEOUT) -> PatternConfig:
        """Retrieves the configuration of the specified pattern from the controller and caches the data"""
        return self.get_pattern_configs([pattern], timeout)[pattern]

    def get_pattern_configs(self, patterns: List[str]=None, timeout: Optional[float]=DEFAULT_TIMEOUT) -> Dict[str, PatternConfig]:
        """Retrieves the configurations for the specified patterns (or all patterns if not provided) from the controller and caches the data"""
        try:
            if not patterns:
                # clear the cache for a full refresh (ensures deleted records do not remain)
                self.__cache.pattern_config_data.clear()
            patterns = validate_patterns(patterns, self.pattern_names) if patterns else self.pattern_names
            self.__send(GetPatternConfigRequest(patterns))
            if not self.__cache.pattern_config_data.await_update(timeout, patterns):
                raise JellyFishException(f"Request for the configuration of patterns '{patterns}' timed out")
            return self.__cache.pattern_config_data.get_all_entries()
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while retrieving config data for pattern(s) {patterns}") from e

    def get_zone_state(self, zone: str, timeout: Optional[float]=DEFAULT_TIMEOUT) -> ZoneState:
        """Retrieves the current state of the specified zone from the controller and caches the data"""
        return self.get_zone_states([zone], timeout)[zone]

    def get_zone_states(self, zones: List[str]=None, timeout: Optional[float]=DEFAULT_TIMEOUT) -> Dict[str, ZoneState]:
        """Retrieves the current state of the specified zones (or all zones if not provided) from the controller and caches the data"""
        try:
            if not zones:
                # clear the cache for a full refresh (ensures deleted records do not remain)
                self.__cache.zone_state_data.clear()
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            self.__send(GetZoneStateRequest(zones))
            if not self.__cache.zone_state_data.await_update(timeout, zones):
                raise JellyFishException(f"Request for the state data of zones '{zones}' timed out")
            return self.__cache.zone_state_data.get_all_entries()
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while retrieving the state of zone(s) {zones}") from e

    def get_calendar_schedule(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> List[ScheduleEvent]:
        """Retrieves the current calendar event schedule from the controller and caches the data"""
        try:
            self.__send(GetCalendarScheduleRequest())
            if not self.__cache.calendar_schedule_data.await_update(timeout):
                raise JellyFishException("Request for calendar schedule data timed out")
            return self.__cache.calendar_schedule_data.get_entry()
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving calendar schedule data") from e

    def get_daily_schedule(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> List[ScheduleEvent]:
        """Retrieves the current daily event schedule from the controller and caches the data"""
        try:
            self.__send(GetDailyScheduleRequest())
            if not self.__cache.daily_schedule_data.await_update(timeout):
                raise JellyFishException("Request for daily schedule data timed out")
            return self.__cache.daily_schedule_data.get_entry()
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving daily schedule data") from e

    def __turn_on_off(self, on: bool, zones: List[str], sync: bool, timeout: float) -> None:
        """Convenience function that turns zones on or off"""
        try:
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            self.__send(SetZoneStateRequest(state=int(on), zoneName=zones))
            if sync and not self.__cache.zone_state_data.await_update(timeout, zones):
                raise JellyFishException(f"Request to turn {'on' if on else 'off'} zones '{zones}' timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while turning {'on' if on else 'off'} zone(s) {zones}") from e

    def turn_on(self, zones: List[str]=None, sync: bool=True, timeout: float=DEFAULT_TIMEOUT) -> None:
        """
        Turns on the provided zone(s) (or all zones if not provided). If sync is set to True (the default),
        the function call will not return until a confirmation response is received from the controller or the request times out.
        """
        self.__turn_on_off(True, zones, sync, timeout)

    def turn_off(self, zones: List[str]=None, sync: bool=True, timeout: float=DEFAULT_TIMEOUT) -> None:
        """
        Turns off the provided zone(s) (or all zones if not provided). If sync is set to True (the default),
        the function call will not return until a confirmation response is received from the controller or the request times out.
        """
        self.__turn_on_off(False, zones, sync, timeout)

    def apply_light_string(self, light_string: List[Tuple[int, int, int]], brightness: int=100, zones: List[str]=None, sync: bool=True, timeout: float=DEFAULT_TIMEOUT) -> None:
        """
        Sets lights in the provided zone(s) to a custom string of colors at the given brightness (or all zones
        if not provided. Default brighness=100%). If sync is set to True (the default), the function call will
        not return until a confirmation response is received from the controller or the request times out.
        """
        try:
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            validate_brightness(brightness)
            colors = [0,0,0]
            colors_pos = [-1]
            for i, rgb in enumerate(light_string):
                validate_rgb(rgb)
                colors.extend(rgb)
                colors_pos.append(i)
            config = PatternConfig(type="Soffit", colors=colors, colorPos=colors_pos, runData=RunConfig(brightness=brightness))
            self.__send(SetZoneStateRequest(state=1, zoneName=zones, data=config))
            if sync and not self.__cache.zone_state_data.await_update(timeout, zones):
                raise JellyFishException(f"Request to apply light string on zones {zones} timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while applying light string to zone(s) {zones}") from e

    def apply_color(self, rgb: Tuple[int, int, int], brightness: int=100, zones: List[str]=None, sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Sets all lights in the provided zone(s) to a solid color at the given brightness (or all zones if not provided. Default brighness=100%)"""
        try:
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            validate_rgb(rgb)
            validate_brightness(brightness)
            config = PatternConfig(type="Color", colors=[*rgb], runData=RunConfig(brightness=brightness))
            self.__send(SetZoneStateRequest(state=1, zoneName=zones, data=config))
            if sync and not self.__cache.zone_state_data.await_update(timeout, zones):
                raise JellyFishException(f"Request to apply color {color} on zones {zones} timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while applying color to zone(s) {zones}") from e

    def apply_pattern(self, pattern: str, zones: List[str]=None, sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Activates a predefined pattern on the provided zone(s) (or all zones if not provided)"""
        try:
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            validate_patterns([pattern], self.pattern_names)
            self.__send(SetZoneStateRequest(state=1, zoneName=zones, file=pattern))
            if sync and not self.__cache.zone_state_data.await_update(timeout, zones):
                raise JellyFishException(f"Request to apply pattern '{pattern}' on zones {zones} timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while applying pattern to zone(s) {zones}") from e

    def apply_pattern_config(self, config: PatternConfig, zones: List[str]=None, sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Activates a pattern configuration on the provided zone(s) (or all zones if not provided)"""
        try:
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            validate_pattern_config(config, zones)
            self.__send(SetZoneStateRequest(state=1, zoneName=zones, data=config))
            if sync and not self.__cache.zone_state_data.await_update(timeout, zones):
                raise JellyFishException(f"Request to apply pattern config on zones '{zones}' timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while applying pattern config to zone(s) {zones}") from e

    def save_pattern(self, pattern: str, config: PatternConfig, sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Creates or updates a pattern file"""
        try:
            validate_pattern_config(config, self.zone_names)
            pattern = Pattern.from_str(pattern) if pattern not in self.pattern_names else next(p for p in self.pattern_list if str(p) == pattern)
            if pattern.readOnly:
                raise JellyFishException(f"Cannot update pattern '{pattern}' because it is read only")
            self.__send(SetPatternConfigRequest(pattern=pattern, jsonData=config))
            if sync and not self.__cache.pattern_config_data.await_update(timeout, [str(pattern)]):
                raise JellyFishException(f"Request to save pattern '{str(pattern)}' timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while saving pattern '{pattern}' config: {config}") from e

    def delete_pattern(self, pattern: str, sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Deletes a pattern file or folder"""
        try:
            patterns = self.pattern_list
            pattern_obj = next((p for p in patterns if str(p) == pattern), None)
            if not pattern_obj:
                raise JellyFishException(f"Cannot delete pattern '{pattern}' because it does not exist")
            if pattern_obj.readOnly:
                raise JellyFishException(f"Cannot delete pattern '{pattern}' because it is read only")
            self.__send(DeletePatternRequest(pattern_obj))
            if sync and not self.__cache.pattern_list_data.await_update(timeout, [pattern]):
                raise JellyFishException(f"Request to delete pattern '{pattern}' timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while deleting pattern '{pattern}'") from e

    def add_calendar_event(self, event: ScheduleEvent, sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Adds a calendar event to the schedule"""
        events = self.calendar_schedule
        events.append(event)
        self.set_calendar_schedule(events, sync, timeout)

    def set_calendar_schedule(self, events: List[ScheduleEvent], sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Saves the schedule of calendar events. WARNING: this list must include all calendar events in the entire schedule! Any events not included will be deleted"""
        try:
            patterns = self.pattern_names
            zones = self.zone_names
            for event in events:
                validate_schedule_event(event, True, patterns, zones)
            self.__send(SetCalendarScheduleRequest(events))
            if sync and not self.__cache.calendar_schedule_data.await_update(timeout):
                raise JellyFishException("Request for calendar schedule data timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while saving calendar event schedule") from e

    def add_daily_event(self, event: ScheduleEvent, sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Adds a daily event to the schedule"""
        events = self.daily_schedule
        events.append(event)
        self.set_daily_schedule(events, sync, timeout)

    def set_daily_schedule(self, events: List[ScheduleEvent], sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Saves the schedule of daily events. WARNING: this list must include all daily events in the entire schedule! Any events not included will be deleted"""
        try:
            patterns = self.pattern_names
            zones = self.zone_names
            for event in events:
                validate_schedule_event(event, False, patterns, zones)
            self.__send(SetDailyScheduleRequest(events))
            if sync and not self.__cache.daily_schedule_data.await_update(timeout):
                raise JellyFishException("Request for daily schedule data timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while saving daily event schedule") from e

    def add_zone(self, zone: str, config: ZoneConfig, sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Adds a zone configuration"""
        configs = self.zone_configs
        if zone in configs:
            raise JellyFishException(f"Error encountered while adding a zone configuration: zone name '{zone}' already exists")
        configs[zone] = config
        self.set_zone_configs(configs, sync, timeout)

    def delete_zone(self, zone: str, sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Deletes a zone configuration"""
        configs = self.zone_configs
        if zone not in configs:
            raise JellyFishException(f"Error encountered while deleting a zone configuration: zone name '{zone}' does not exist")
        del configs[zone]
        self.set_zone_configs(configs, sync, timeout)

    def set_zone_configs(self, zone_configs: Dict[str, ZoneConfig], sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Saves zone configurations. WARNING: this list must include all zones! Any zones not included will be deleted"""
        try:
            # Do some reasonable data defaulting
            for config in zone_configs.values():
                config.numPixels = 0
                for mapping in config.portMap:
                    mapping.ctlrName = mapping.ctlrName or self.hostname
                    config.numPixels += abs(mapping.phyEndIdx - mapping.phyStartIdx) + 1
                validate_zone_config(config)
            self.__send(SetZoneConfigRequest(zone_configs))
            if sync and not self.__cache.zone_config_data.await_update(timeout, zone_configs.keys()):
                raise JellyFishException("Request to set zone configurations timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while saving zone configurations") from e

    def set_name(self, name: str, sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Sets the user-defined name of the controller"""
        try:
            self.__send(SetControllerNameRequest(name))
            if sync and not self.__cache.name_data.await_update(timeout):
                raise JellyFishException("Request to set controller name timed out")
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while setting controller name") from e