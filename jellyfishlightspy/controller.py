# https://medium.com/@joel.barmettler/how-to-upload-your-python-package-to-pypi-65edc5fe9c56
#TODO: get rid of above once this is done

import logging
import websocket
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from threading import Thread, Lock
from .const import LOGGER, ZONE_DATA, PATTERN_DATA, ZONE_STATE_DATA, DEFAULT_TIMEOUT
from .model import PatternName, RunData, RunPatternData, StateData, ZoneConfiguration
from .requests import GetRequest, SetRequest
from .helpers import (
    JellyFishLightsException,
    TimelyEvent,
    validate_rgb,
    validate_brightness,
    validate_zones,
    validate_pattern,
    to_json,
    from_json
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
        self.__ws_monitor = WebSocketMonitor(self)

    def __send(self, data: Any) -> None:
        """Sends data to the controller over the web socket connection"""
        if not self.__ws_monitor.connected:
            raise JellyFishLightsException("Not connected to controller")
        msg = to_json(data)
        LOGGER.debug("Sending: %s", msg)
        self.__ws.send(msg)

    @property
    def connected(self) -> bool:
        """Indicates if the the web socket connection to the controller is established"""
        return self.__ws_monitor.connected

    @property
    def zones(self) -> Dict[str, ZoneConfiguration]:
        """The current zones and their configuration (returns cached data if available)"""
        if len(self.__ws_monitor.zones) == 0:
            return self.get_zones()
        return self.__ws_monitor.zones

    @property
    def zone_names(self) -> List[str]:
        """The current zone names (returns cached data if available)"""
        return list(self.zones)

    @property
    def patterns(self) -> List[PatternName]:
        """The list of preset patterns (returns cached data if available)"""
        if len(self.__ws_monitor.patterns) == 0:
            return self.get_patterns()
        return self.__ws_monitor.patterns

    @property
    def pattern_names(self) -> List[str]:
        """The current pattern names (returns cached data if available)"""
        return [str(p) for p in self.patterns if p.name]

    @property
    def zone_states(self) -> Dict[str, StateData]:
        """The state of each zone (returns cached data if available)"""
        if len(self.__ws_monitor.zone_states) == 0:
            return self.get_zone_states()
        return self.__ws_monitor.zone_states

    def get_zones(self, timeout: Optional[float] = DEFAULT_TIMEOUT) -> Dict:
        """Retrieves the list of current zones and their configuration from the controller and caches the data"""
        try:
            self.__send(GetRequest([ZONE_DATA]))
            self.__ws_monitor.await_zone_data(timeout)
            return self.__ws_monitor.zones
        except JellyFishLightsException:
            raise
        except Exception as e:
            raise JellyFishLightsException("Error encountered while retrieving zone data") from e

    def get_patterns(self, timeout: Optional[float] = DEFAULT_TIMEOUT) -> List[PatternName]:
        """Retrieves the list of preset patterns from the controller and caches the data"""
        try:
            self.__send(GetRequest([PATTERN_DATA]))
            self.__ws_monitor.await_pattern_data(timeout)
            return self.__ws_monitor.patterns
        except JellyFishLightsException:
            raise
        except Exception as e:
            raise JellyFishLightsException("Error encountered while retrieving pattern data") from e

    def get_zone_state(self, zone: str, timeout: Optional[float] = DEFAULT_TIMEOUT) -> StateData:
        """Retrieves the current state of the specified zone from the controller and caches the data"""
        return self.get_zone_states([zone], timeout)[zone]

    def get_zone_states(self, zones: List[str] = None, timeout: Optional[float] = DEFAULT_TIMEOUT) -> Dict[str, StateData]:
        """Retrieves the current state of the specified zones (or all zones if not provided) from the controller and caches the data"""
        try:
            zones = zones or list(self.zones)
            validate_zones(zones, self.zones)
            self.__send(GetRequest([ZONE_STATE_DATA, *zones]))
            self.__ws_monitor.await_zone_state_data(zones, timeout)
            return self.__ws_monitor.zone_states
        except JellyFishLightsException:
            raise
        except Exception as e:
            raise JellyFishLightsException(f"Error encountered while retrieving the state of zone(s) {zones}") from e

    def connect(self, timeout: Optional[float] = DEFAULT_TIMEOUT) -> None:
        """Establishes a connection to the JellyFish Lighting controller at the given address and begins listening for messages"""
        try:
            self.__ws = websocket.WebSocketApp(
                f"ws://{self.address}:9000",
                on_open = self.__ws_monitor.on_open,
                on_close = self.__ws_monitor.on_close,
                on_message = self.__ws_monitor.on_message
            )
            self.__ws_thread = Thread(target=lambda: self.__ws.run_forever(), daemon=True)
            self.__ws_thread.start()
            self.__ws_monitor.await_connection(timeout)
        except JellyFishLightsException:
            raise
        except Exception as e:
            raise JellyFishLightsException(f"Could not connect to controller at {self.address}") from e

    def disconnect(self, timeout: Optional[float] = DEFAULT_TIMEOUT):
        """Disconnects from the JellyFish Lighting controller"""
        try:
            self.__ws.close()
            self.__ws_thread.join(timeout)
            if self.__ws_thread.is_alive():
                raise JellyFishLightsException(f"Attempt to disconnect from controller at {self.address} timed out")
        except JellyFishLightsException:
            raise
        except Exception as e:
            raise JellyFishLightsException(f"Error encountered while disconnecting from controller at {self.address}") from e

    def __turn_on_off(self, on: bool, zones: List[str], sync: bool, timeout: float) -> None:
        """Convenience function that turns zones on or off"""
        try:
            zones = zones or list(self.zones)
            validate_zones(zones, self.zones)
            req = SetRequest(
                state = int(on),
                zoneName = zones
            )
            self.__send(req)
            if sync:
                self.__ws_monitor.await_zone_state_data(zones, timeout)
        except JellyFishLightsException:
            raise
        except Exception as e:
            raise JellyFishLightsException(f"Error encountered while turning {'on' if on else 'off'} zone(s) {zones}") from e

    def turn_on(self, zones: List[str] = None, sync: bool = True, timeout: float = DEFAULT_TIMEOUT) -> None:
        """
        Turns on the provided zone(s) (or all zones if not provided). If sync is set to True (the default),
        the function call will not return until a confirmation response is received from the controller or the request times out.
        """
        self.__turn_on_off(True, zones, sync, timeout)

    def turn_off(self, zones: List[str] = None, sync: bool = True, timeout: float = DEFAULT_TIMEOUT) -> None:
        """
        Turns off the provided zone(s) (or all zones if not provided). If sync is set to True (the default),
        the function call will not return until a confirmation response is received from the controller or the request times out.
        """
        self.__turn_on_off(False, zones, sync, timeout)

    def apply_light_string(self, light_string: List[Tuple[int, int, int]], brightness: int = 100, zones: List[str] = None, sync: bool = True, timeout: float = DEFAULT_TIMEOUT) -> None:
        """
        Sets lights in the provided zone(s) to a custom string of colors at the given brightness (or all zones
        if not provided). If sync is set to True (the default), the function call will not return until a
        confirmation response is received from the controller or the request times out.
        """
        try:
            zones = zones or list(self.zones)
            validate_zones(zones, self.zones)
            validate_brightness(brightness)
            colors = [0,0,0]
            colors_pos = [-1]
            for i, rgb in enumerate(light_string):
                validate_rgb(rgb)
                colors.extend(rgb)
                colors_pos.append(i)

            rd = RunData(speed = 0, brightness = brightness, effect = "No Effect", effectValue = 0, rgbAdj = [100, 100, 100])
            rpd = RunPatternData(colors = colors, colorPos = colors_pos, runData = rd, type = "Soffit")

            req = SetRequest(
                state = 3,
                zoneName = zones,
                data = rpd
            )
            self.__send(req)
            if sync:
                self.__ws_monitor.await_zone_state_data(zones, timeout)
        except JellyFishLightsException:
            raise
        except Exception as e:
            raise JellyFishLightsException(f"Error encountered while applying light string to zone(s) {zones}") from e

    def apply_color(self, rgb: Tuple[int,int,int], brightness: int = 100, zones: List[str] = None, sync: bool = True, timeout: float = DEFAULT_TIMEOUT):
        """Sets all lights in the provided zone(s) to a solid color at the given brightness (or all zones if not provided. Default brighness = 100%)"""
        try:
            zones = zones or list(self.zones)
            validate_zones(zones, self.zones)
            validate_rgb(rgb)
            validate_brightness(brightness)
            rd = RunData(speed = 10, brightness = brightness, effect = "No Effect", effectValue = 0, rgbAdj = [100, 100, 100])
            rpd = RunPatternData(colors = [*rgb], type = "Color", skip = 1, direction = "Left", runData = rd)

            req = SetRequest(
                state = 1,
                zoneName = zones,
                data = rpd
            )
            self.__send(req)
            if sync:
                self.__ws_monitor.await_zone_state_data(zones, timeout)
        except JellyFishLightsException:
            raise
        except Exception as e:
            raise JellyFishLightsException(f"Error encountered while applying color to zone(s) {zones}") from e

    def apply_pattern(self, pattern: str, zones: List[str] = None, sync: bool = True, timeout: float = DEFAULT_TIMEOUT):
        """Activates a predefined pattern on the provided zone(s)"""
        try:
            zones = zones or list(self.zones)
            validate_zones(zones, self.zones)
            validate_pattern(pattern, self.patterns)
            req = SetRequest(
                state = 1,
                zoneName = zones,
                file = pattern
            )
            self.__send(req)
            if sync:
                self.__ws_monitor.await_zone_state_data(zones, timeout)
        except JellyFishLightsException:
            raise
        except Exception as e:
            raise JellyFishLightsException(f"Error encountered while applying pattern to zone(s) {zones}") from e

class WebSocketMonitor:

    def __init__(self, controller: JellyFishController):
        self.__controller = controller
        self.__zones: Dict[str, ZoneConfiguration] = {}
        self.__patterns: List[PatternName] = []
        self.__zone_states: Dict[str, StateData] = {}
        self.__connected: TimelyEvent = TimelyEvent()
        self.__events = {
            ZONE_DATA: TimelyEvent(),
            PATTERN_DATA: TimelyEvent(),
            ZONE_STATE_DATA: {}
        }
        self.__locks = {
            ZONE_DATA: Lock(),
            PATTERN_DATA: Lock(),
            ZONE_STATE_DATA: Lock()
        }

    def __get_run_pattern_event(self, zone: str) -> TimelyEvent:
        """Returns the TimelyEvent object that notifies when new RunPattern data is available for a zone"""
        if zone not in self.__events[ZONE_STATE_DATA]:
            self.__events[ZONE_STATE_DATA][zone] = TimelyEvent()
        return self.__events[ZONE_STATE_DATA][zone]

    def __trigger_event(self, data_key: str, zone: Optional[str] = None) -> None:
        """Triggers a TimelyEvent object to notify the main thread when new  data is available"""
        event = self.__events[data_key] if zone is None else self.__get_run_pattern_event(zone)
        event.set()
        event.clear()

    @property
    def connected(self) -> bool:
        """Returns true if the the web socket connection to the controller is established"""
        return self.__connected.is_set()

    @property
    def zones(self) -> Dict[str, ZoneConfiguration]:
        """The current zones and their configuration. Ensures thread safe access via Locks"""
        with self.__locks[ZONE_DATA]:
            return self.__zones

    @property
    def patterns(self) -> List[PatternName]:
        """The list of preset patterns currently available. Ensures thread safe access via Locks"""
        with self.__locks[PATTERN_DATA]:
            return self.__patterns

    @property
    def zone_states(self) -> Dict[str, StateData]:
        """The state of each zone. Ensures thread safe access via Locks"""
        with self.__locks[ZONE_STATE_DATA]:
            return self.__zone_states

    def await_connection(self, timeout: float) -> None:
        if not self.__connected.wait(timeout=timeout):
            raise JellyFishLightsException(f"Connection to controller at {self.__controller.address} timed out")

    def await_zone_data(self, timeout: float) -> None:
        if not self.__events[ZONE_DATA].wait(timeout=timeout):
            raise JellyFishLightsException("Request for zone data timed out")

    def await_pattern_data(self, timeout: float) -> None:
        if not self.__events[PATTERN_DATA].wait(timeout=timeout):
            raise JellyFishLightsException("Request for pattern data timed out")

    def await_zone_state_data(self, zones: List[str], timeout: float):
        start = time.perf_counter()
        for zone in zones:
            event = self.__get_run_pattern_event(zone)
            timeout_remaining = timeout - (time.perf_counter() - start)
            if not event.wait(timeout = timeout_remaining if timeout_remaining > 0 else 0, after_ts = start):
                raise JellyFishLightsException(f"Request for the state data of zones '{zones}' timed out")

    def on_open(self, ws):
        """Callback method that is invoked when the web socket connection is opened"""
        LOGGER.debug("Connected to the JellyFish Lighting controller at %s", self.__controller.address)
        self.__connected.set()

    def on_close(self, ws, status, message):
        """Callback method that is invoked when the web socket connection is closed"""
        LOGGER.debug("Disconnected from the JellyFish Lighting controller at %s", self.__controller.address)
        self.__connected.clear()

    def on_message(self, ws, message):
        """Callback method that is invoked when data is received over the web socket connection"""
        LOGGER.debug("Recieved: %s", message)
        try:
            data = from_json(message)
            if ZONE_DATA in data:
                with self.__locks[ZONE_DATA]:
                    self.__zones = data[ZONE_DATA]
                self.__trigger_event(ZONE_DATA)
            elif PATTERN_DATA in data:
                with self.__locks[PATTERN_DATA]:
                    self.__patterns = data[PATTERN_DATA]
                self.__trigger_event(PATTERN_DATA)
            elif ZONE_STATE_DATA in data:
                state = data[ZONE_STATE_DATA]
                with self.__locks[ZONE_STATE_DATA]:
                    for zone in state.zoneName:
                        self.__zone_states[zone] = state
                        self.__trigger_event(ZONE_STATE_DATA, zone)
        except Exception:
            LOGGER.exception("Error encountered while processing websocket data")