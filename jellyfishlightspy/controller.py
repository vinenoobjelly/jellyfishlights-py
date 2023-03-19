# https://medium.com/@joel.barmettler/how-to-upload-your-python-package-to-pypi-65edc5fe9c56
#TODO: get rid of above once this is done

import logging
import websocket
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from threading import Thread, Lock
from .const import LOGGER, ZONE_DATA, PATTERN_DATA, PATTERN_CONFIG_DATA, STATE_DATA, DEFAULT_TIMEOUT
from .model import Pattern, RunConfig, PatternConfig, State, ZoneConfig
from .requests import GetRequest, SetStateRequest
from .helpers import (
    JellyFishException,
    TimelyEvent,
    validate_rgb,
    validate_brightness,
    validate_zones,
    validate_patterns,
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
        self.__ws_monitor = WebSocketMonitor(address)

    @property
    def connected(self) -> bool:
        """Indicates if the the web socket connection to the controller is established"""
        return self.__ws_monitor.connected

    @property
    def zones(self) -> Dict[str, ZoneConfig]:
        """The current zones and their configuration (returns cached data if available)"""
        if len(self.__ws_monitor.zones) == 0:
            return self.get_zones()
        return self.__ws_monitor.zones

    @property
    def zone_names(self) -> List[str]:
        """The current zone names (returns cached data if available)"""
        return list(self.zones)

    @property
    def patterns(self) -> List[Pattern]:
        """The list of preset patterns, including folders (returns cached data if available)"""
        if len(self.__ws_monitor.patterns) == 0:
            return self.get_patterns()
        return self.__ws_monitor.patterns

    @property
    def pattern_names(self) -> List[str]:
        """The current pattern names, excluding folders (returns cached data if available)"""
        return [str(p) for p in self.patterns if not p.is_folder]

    @property
    def pattern_configs(self) -> Dict[str, PatternConfig]:
        """The current pattern configurations, excluding folders (returns cached data if available)"""
        if len(self.__ws_monitor.pattern_configs) == 0:
            return self.get_pattern_configs()
        return self.__ws_monitor.pattern_configs

    @property
    def zone_states(self) -> Dict[str, State]:
        """The state of each zone (returns cached data if available)"""
        if len(self.__ws_monitor.zone_states) == 0:
            return self.get_zone_states()
        return self.__ws_monitor.zone_states

    def connect(self, timeout: Optional[float] = DEFAULT_TIMEOUT) -> None:
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

    def disconnect(self, timeout: Optional[float] = DEFAULT_TIMEOUT):
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

    def get_zones(self, timeout: Optional[float] = DEFAULT_TIMEOUT) -> Dict[str, ZoneConfig]:
        """Retrieves the list of current zones and their configuration from the controller and caches the data"""
        try:
            self.__send(GetRequest(ZONE_DATA))
            self.__ws_monitor.await_zone_data(timeout)
            return self.__ws_monitor.zones
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving zone data") from e

    def get_patterns(self, timeout: Optional[float] = DEFAULT_TIMEOUT) -> List[Pattern]:
        """Retrieves the list of preset patterns from the controller and caches the data"""
        try:
            self.__send(GetRequest(PATTERN_DATA))
            self.__ws_monitor.await_pattern_data(timeout)
            return self.__ws_monitor.patterns
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException("Error encountered while retrieving pattern data") from e

    def get_pattern_config(self, pattern: str, timeout: Optional[float] = DEFAULT_TIMEOUT) -> PatternConfig:
        """Retrieves the configuration of the specified pattern from the controller and caches the data"""
        return self.get_pattern_configs([pattern], timeout)[pattern]

    def get_pattern_configs(self, patterns: List[str] = None, timeout: Optional[float] = DEFAULT_TIMEOUT) -> List[PatternConfig]:
        """Retrieves the configurations for the specified patterns (or all patterns if not provided) from the controller and caches the data"""
        try:
            patterns = validate_patterns(patterns, self.pattern_names) if patterns else self.pattern_names
            args = []
            for pattern in patterns:
                pobj = Pattern.from_str(pattern)
                args.extend([pobj.folders, pobj.name])
            self.__send(GetRequest(PATTERN_CONFIG_DATA, *args))
            self.__ws_monitor.await_pattern_config_data(patterns, timeout)
            return self.__ws_monitor.pattern_configs
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while retrieving config data for pattern(s) {patterns}") from e

    def get_zone_state(self, zone: str, timeout: Optional[float] = DEFAULT_TIMEOUT) -> State:
        """Retrieves the current state of the specified zone from the controller and caches the data"""
        return self.get_zone_states([zone], timeout)[zone]

    def get_zone_states(self, zones: List[str] = None, timeout: Optional[float] = DEFAULT_TIMEOUT) -> Dict[str, State]:
        """Retrieves the current state of the specified zones (or all zones if not provided) from the controller and caches the data"""
        try:
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            self.__send(GetRequest(STATE_DATA, *zones))
            self.__ws_monitor.await_zone_state_data(zones, timeout)
            return self.__ws_monitor.zone_states
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while retrieving the state of zone(s) {zones}") from e

    def __turn_on_off(self, on: bool, zones: List[str], sync: bool, timeout: float) -> None:
        """Convenience function that turns zones on or off"""
        try:
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            req = SetStateRequest(
                state = int(on),
                zoneName = zones
            )
            self.__send(req)
            if sync:
                self.__ws_monitor.await_zone_state_data(zones, timeout)
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while turning {'on' if on else 'off'} zone(s) {zones}") from e

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
        if not provided. Default brighness = 100%). If sync is set to True (the default), the function call will
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

            rc = RunConfig(speed = 0, brightness = brightness, effect = "No Effect", effectValue = 0, rgbAdj = [100, 100, 100])
            pc = PatternConfig(colors = colors, colorPos = colors_pos, runData = rc, type = "Soffit")

            req = SetStateRequest(
                state = 3,
                zoneName = zones,
                data = pc
            )
            self.__send(req)
            if sync:
                self.__ws_monitor.await_zone_state_data(zones, timeout)
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while applying light string to zone(s) {zones}") from e

    def apply_color(self, rgb: Tuple[int, int, int], brightness: int = 100, zones: List[str] = None, sync: bool = True, timeout: float = DEFAULT_TIMEOUT):
        """Sets all lights in the provided zone(s) to a solid color at the given brightness (or all zones if not provided. Default brighness = 100%)"""
        try:
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            validate_rgb(rgb)
            validate_brightness(brightness)
            rc = RunConfig(speed = 10, brightness = brightness, effect = "No Effect", effectValue = 0, rgbAdj = [100, 100, 100])
            pc = PatternConfig(colors = [*rgb], type = "Color", skip = 1, direction = "Left", runData = rc)

            req = SetStateRequest(
                state = 1,
                zoneName = zones,
                data = pc
            )
            self.__send(req)
            if sync:
                self.__ws_monitor.await_zone_state_data(zones, timeout)
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while applying color to zone(s) {zones}") from e

    def apply_pattern(self, pattern: str, zones: List[str] = None, sync: bool = True, timeout: float = DEFAULT_TIMEOUT):
        """Activates a predefined pattern on the provided zone(s)"""
        try:
            zones = validate_zones(zones, self.zone_names) if zones else self.zone_names
            validate_patterns([pattern], self.pattern_names)
            req = SetStateRequest(
                state = 1,
                zoneName = zones,
                file = pattern
            )
            self.__send(req)
            if sync:
                self.__ws_monitor.await_zone_state_data(zones, timeout)
        except JellyFishException:
            raise
        except Exception as e:
            raise JellyFishException(f"Error encountered while applying pattern to zone(s) {zones}") from e

class WebSocketMonitor:

    def __init__(self, address: str):
        self.__address = address
        self.__zones: Dict[str, ZoneConfig] = {}
        self.__patterns: List[Pattern] = []
        self.__zone_states: Dict[str, State] = {}
        self.__pattern_configs: Dict[str, PatternConfig] = {}
        self.__connected: TimelyEvent = TimelyEvent()
        self.__events = {
            ZONE_DATA: TimelyEvent(),
            PATTERN_DATA: TimelyEvent(),
            STATE_DATA: {},
            PATTERN_CONFIG_DATA: {},
        }
        self.__locks = {
            ZONE_DATA: Lock(),
            PATTERN_DATA: Lock(),
            STATE_DATA: Lock(),
            PATTERN_CONFIG_DATA: Lock(),
        }

    def __get_entity_event(self, data_key: str, entity_key: str) -> TimelyEvent:
        """
        Returns the TimelyEvent object that notifies when new entity data is available.
        For example, new State data for a zone, or new PatternConfig data for a pattern.
        """
        if entity_key not in self.__events[data_key]:
            self.__events[data_key][entity_key] = TimelyEvent()
        return self.__events[data_key][entity_key]

    def __trigger_event(self, data_key: str, entity_key: Optional[str] = None) -> None:
        """Triggers a TimelyEvent object to notify the main thread when new data is available"""
        event = self.__get_entity_event(data_key, entity_key) if entity_key else self.__events[data_key]
        event.set()
        event.clear()

    @property
    def connected(self) -> bool:
        """Returns true if the the web socket connection to the controller is established"""
        return self.__connected.is_set()

    @property
    def zones(self) -> Dict[str, ZoneConfig]:
        """The current zones and their configuration. Ensures thread safe access via Locks"""
        with self.__locks[ZONE_DATA]:
            return self.__zones

    @property
    def patterns(self) -> List[Pattern]:
        """The list of preset patterns currently available. Ensures thread safe access via Locks"""
        with self.__locks[PATTERN_DATA]:
            return self.__patterns

    @property
    def pattern_configs(self) -> Dict[str, PatternConfig]:
        """The pattern configurations currently available. Ensures thread safe access via Locks"""
        with self.__locks[PATTERN_CONFIG_DATA]:
            return self.__pattern_configs

    @property
    def zone_states(self) -> Dict[str, State]:
        """The state of each zone. Ensures thread safe access via Locks"""
        with self.__locks[STATE_DATA]:
            return self.__zone_states

    def await_connection(self, timeout: float) -> None:
        """Waits for a connection to the controler to be established. Raises a JellyFishException upon timeout"""
        if not self.__connected.wait(timeout=timeout):
            raise JellyFishException(f"Connection to controller at {self.__address} timed out")

    def await_zone_data(self, timeout: float) -> None:
        """Waits for new zone data to be received from the controller. Raises a JellyFishException upon timeout"""
        if not self.__events[ZONE_DATA].wait(timeout=timeout):
            raise JellyFishException("Request for zone data timed out")

    def await_pattern_data(self, timeout: float) -> None:
        """Waits for new pattern data to be received from the controller. Raises a JellyFishException upon timeout"""
        if not self.__events[PATTERN_DATA].wait(timeout=timeout):
            raise JellyFishException("Request for pattern data timed out")

    def await_zone_state_data(self, zones: List[str], timeout: float) -> None:
        """Waits for new zone state data to be received from the controller. Raises a JellyFishException upon timeout"""
        self.__await_multiple(STATE_DATA, zones, timeout, f"Request for the state data of zones '{zones}' timed out")

    def await_pattern_config_data(self, pattern_names: List[str], timeout: float) -> None:
        """Waits for new pattern config data to be received from the controller. Raises a JellyFishException upon timeout"""
        self.__await_multiple(PATTERN_CONFIG_DATA, pattern_names, timeout, f"Request for the configuration of patterns '{pattern_names}' timed out")

    def __await_multiple(self, data_key: str, entity_keys: List[str], timeout: float, timeout_msg: str) -> None:
        """Convenience function that waits for multiple events to occur. Raises a JellyFishException upon timeout"""
        start_ts = time.perf_counter()
        events = [self.__get_entity_event(data_key, entity_key) for entity_key in entity_keys]
        for event in events:
            # We cannot simply wait for each event sequentially because messages can be received simultaneously and out of order.
            # To overcome this, use the TimelyEvent timestamp to check if data has been received since this function was called.
            timeout_remaining = timeout - (time.perf_counter() - start_ts) # Decrement the timeout as we wait for each event
            if not event.wait(timeout = timeout_remaining, after_ts = start_ts):
                raise JellyFishException(timeout_msg)

    def on_open(self, ws):
        """Callback method that is invoked when the web socket connection is opened"""
        LOGGER.debug("Connected to the JellyFish Lighting controller at %s", self.__address)
        self.__connected.set()

    def on_close(self, ws, status, message):
        """Callback method that is invoked when the web socket connection is closed"""
        LOGGER.debug("Disconnected from the JellyFish Lighting controller at %s", self.__address)
        self.__connected.clear()

    def on_message(self, ws, message):
        """Callback method that is invoked when data is received over the web socket connection"""
        LOGGER.debug("Recieved: %s", message)
        try:
            # Parse the data
            data = from_json(message)
            if data["cmd"] != "fromCtlr":
                return

            # Check what type of data the message contains (zones, patterns, or states).
            # Then, update cached data in a thread safe manner (using locks) and trigger
            # events to let listeners/waiters know that new data has been received
            if ZONE_DATA in data:
                with self.__locks[ZONE_DATA]:
                    self.__zones = data[ZONE_DATA]
                self.__trigger_event(ZONE_DATA)

            elif PATTERN_DATA in data:
                with self.__locks[PATTERN_DATA]:
                    self.__patterns = data[PATTERN_DATA]
                self.__trigger_event(PATTERN_DATA)

            elif STATE_DATA in data:
                state = data[STATE_DATA]
                with self.__locks[STATE_DATA]:
                    for zone in state.zoneName:
                        self.__zone_states[zone] = state
                        self.__trigger_event(STATE_DATA, zone)

            elif PATTERN_CONFIG_DATA in data:
                pattern_config = data[PATTERN_CONFIG_DATA]
                pattern = Pattern(pattern_config["folders"], pattern_config["name"])
                with self.__locks[PATTERN_CONFIG_DATA]:
                    self.__pattern_configs[str(pattern)] = pattern_config["jsonData"]
                self.__trigger_event(PATTERN_CONFIG_DATA, str(pattern))
        except Exception:
            LOGGER.exception("Error encountered while processing web socket message: '%s'", message)

    def on_error(self, ws, error):
        """Callback method that is invoked when the web socket connection encounters an error"""
        LOGGER.error("Web socket connection to the JellyFish Lighting controller at %s encountered an error: %s", self.__address, error)