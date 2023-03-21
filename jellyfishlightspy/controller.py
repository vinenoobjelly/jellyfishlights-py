# https://medium.com/@joel.barmettler/how-to-upload-your-python-package-to-pypi-65edc5fe9c56
#TODO: get rid of above once this is done

import websocket
from typing import Dict, List, Tuple, Optional, Any
from threading import Thread
from .const import LOGGER, DEFAULT_TIMEOUT
from .model import Pattern, RunConfig, PatternConfig, ZoneState, ZoneConfig, ControllerVersion
from .monitor import WebSocketMonitor
from .requests import (
    GetControllerVersionRequest,
    GetZoneConfigRequest,
    GetZoneStateRequest,
    GetPatternListRequest,
    GetPatternConfigRequest,
    SetZoneStateRequest,
    SetPatternConfigRequest,
    DeletePatternRequest,
)
from .helpers import (
    JellyFishException,
    validate_rgb,
    validate_brightness,
    validate_zones,
    validate_patterns,
    validate_pattern_config,
    to_json,
)

#TODO: adding and setting patterns, schedules, and zones
#TODO: get current schedule

# Silence warning message when websocket connects
websocket.enableTrace(True, level="ERROR")

class JellyFishController:
    """Manages connectivity and data transfer to/from a JellyFish Lighting Controller"""

    def __init__(self, address: str):
        self.address = address
        self.__ws: websocket.WebSocketApp
        self.__ws_thread: Thread
        self.__ws_monitor = WebSocketMonitor(address)

    def __repr__(self):
        return self.__class__.__name__ + str({"address": self.address, "connected": self.connected})

    @property
    def connected(self) -> bool:
        """Indicates if the the web socket connection to the controller is established"""
        return self.__ws_monitor.connected

    @property
    def controller_version(self) -> ControllerVersion:
        """The controller's version information (returns cached data if available)"""
        if not self.__ws_monitor.controller_version:
            return self.get_controller_version()
        return self.__ws_monitor.controller_version

    @property
    def zone_configs(self) -> Dict[str, ZoneConfig]:
        """The current zones and their configuration (returns cached data if available)"""
        if len(self.__ws_monitor.zone_configs) == 0:
            return self.get_zone_configs()
        return self.__ws_monitor.zone_configs

    @property
    def zone_names(self) -> List[str]:
        """The current zone names (returns cached data if available)"""
        return list(self.zone_configs)

    @property
    def pattern_list(self) -> List[Pattern]:
        """The list of preset patterns, including folders (returns cached data if available)"""
        if len(self.__ws_monitor.pattern_list) == 0:
            return self.get_pattern_list()
        return list(self.__ws_monitor.pattern_list.values())

    @property
    def pattern_names(self) -> List[str]:
        """The current pattern names, excluding folders (returns cached data if available)"""
        return [str(p) for p in self.pattern_list if not p.is_folder]

    @property
    def pattern_configs(self) -> Dict[str, PatternConfig]:
        """The current pattern configurations, excluding folders (returns cached data if available)"""
        if len(self.__ws_monitor.pattern_configs) != len(self.pattern_list):
            return self.get_pattern_configs()
        return self.__ws_monitor.pattern_configs

    @property
    def zone_states(self) -> Dict[str, ZoneState]:
        """The state of each zone (returns cached data if available)"""
        if len(self.__ws_monitor.zone_states) != len(self.zones):
            return self.get_zone_states()
        return self.__ws_monitor.zone_states

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
            self.__ws_thread = Thread(target=lambda: self.__ws.run_forever(), daemon=True)
            self.__ws_thread.start()
            self.__ws_monitor.await_connection(timeout)
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

    def get_controller_version(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> ControllerVersion:
        """Retrieves version information from the controller"""
        try:
            self.__send(GetControllerVersionRequest())
            self.__ws_monitor.await_controller_version_data(timeout)
            return self.__ws_monitor.controller_version
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving zone data") from e

    def get_zone_configs(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> Dict[str, ZoneConfig]:
        """Retrieves the list of current zones and their configuration from the controller and caches the data"""
        try:
            self.__send(GetZoneConfigRequest())
            self.__ws_monitor.await_zone_config_data(timeout)
            return self.__ws_monitor.zone_configs
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving zone data") from e

    def get_pattern_list(self, timeout: Optional[float]=DEFAULT_TIMEOUT) -> List[Pattern]:
        """Retrieves the list of preset patterns from the controller and caches the data"""
        try:
            self.__send(GetPatternListRequest())
            self.__ws_monitor.await_pattern_list_data(timeout)
            return list(self.__ws_monitor.pattern_list.values())
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
                self.__ws_monitor.pattern_configs.clear() # Refresh all cached data
            patterns = validate_patterns(patterns, self.pattern_names) if patterns else self.pattern_names
            self.__send(GetPatternConfigRequest(patterns))
            self.__ws_monitor.await_pattern_config_data(timeout, patterns)
            return self.__ws_monitor.pattern_configs
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
                self.__ws_monitor.zone_states.clear() # Refresh all cached data
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            self.__send(GetZoneStateRequest(zones))
            self.__ws_monitor.await_zone_state_data(timeout, zones)
            return self.__ws_monitor.zone_states
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while retrieving the state of zone(s) {zones}") from e

    def __turn_on_off(self, on: bool, zones: List[str], sync: bool, timeout: float) -> None:
        """Convenience function that turns zones on or off"""
        try:
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            self.__send(SetZoneStateRequest(state=int(on), zoneName=zones))
            if sync:
                self.__ws_monitor.await_zone_state_data(timeout, zones)
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
            self.__send(SetZoneStateRequest(state=3, zoneName=zones, data=config))
            if sync:
                self.__ws_monitor.await_zone_state_data(timeout, zones)
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
            if sync:
                self.__ws_monitor.await_zone_state_data(timeout, zones)
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
            if sync:
                self.__ws_monitor.await_zone_state_data(timeout, zones)
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
            if sync:
                self.__ws_monitor.await_zone_state_data(timeout, zones)
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
            if sync:
                self.__ws_monitor.await_pattern_config_data(timeout, [str(pattern)])
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while saving pattern '{pattern}' config: {config}") from e

    def delete_pattern(self, pattern: str, sync: bool=True, timeout: float=DEFAULT_TIMEOUT):
        """Deletes a pattern file or folder"""
        try:
            patterns = self.get_pattern_list()
            pattern = next((p for p in patterns if str(p) == pattern), None)
            if not pattern:
                raise JellyFishException(f"Cannot delete pattern '{str(pattern)}' because it does not exist")
            if pattern.readOnly:
                raise JellyFishException(f"Cannot delete pattern '{str(pattern)}' because it is read only")
            self.__send(DeletePatternRequest(pattern))
            if sync:
                self.__ws_monitor.await_pattern_list_data(timeout, [str(pattern)])
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while deleting pattern '{pattern}'") from e