# https://medium.com/@joel.barmettler/how-to-upload-your-python-package-to-pypi-65edc5fe9c56
#TODO: get rid of above once this is done

import logging
import websocket
import json
from typing import Dict, List, Tuple, Optional, Any
from threading import Thread, Event, Lock
from .const import LOGGER, ZONE_DATA, PATTERN_LIST_DATA, RUN_PATTERN_DATA, DEFAULT_TIMEOUT
from .model import PatternName, RunData, RunPatternData, StateData
from .requests import GetDataRequest, RunPatternRequest
from .helpers import JellyFishLightsException, wrap_exception, valid_rgb, valid_brightness


#TODO: adding and setting patterns, schedules, and zones
#TODO: get current schedule


class JellyFishController:
    """Manages connectiity and data transfer to/from a JellyFish Lighting Controller"""

    def __init__(self, address: str):
        #TODO: must this be a dict?
        self.zones: Dict = {}
        self.pattern_files: List[PatternName] = []
        self.zone_data: Dict[str, StateData] = {}
        self.__ws: websocket.WebSocketApp
        self.__ws_thread: Thread
        self.__connected: Event = Event()
        self.__address = address
        self.__events = {
            ZONE_DATA: Event(),
            PATTERN_LIST_DATA: Event(),
            RUN_PATTERN_DATA: {}
        }
        self.__locks = {
            ZONE_DATA: Lock(),
            PATTERN_LIST_DATA: Lock(),
            RUN_PATTERN_DATA: Lock()
        }
    
    def __get_run_pattern_event(self, zone: str) -> Event:
        """Returns the Event object that triggers new RunPattern data for a zone"""
        if zone not in self.__events[RUN_PATTERN_DATA]:
            self.__events[RUN_PATTERN_DATA][zone] = Event()
        return self.__events[RUN_PATTERN_DATA][zone]
    
    def __trigger_event(self, dataKey, zone = None):
        """Triggers an Event to notify the main thread when new RunPattern data is available for the zone"""
        event = self.__events[dataKey] if zone is None else self.__get_run_pattern_event(zone)
        event.set()
        event.clear()
    
    def __ws_on_open(self, ws):
        """Callback method that is envoked when the web socket connection is opened"""
        self.__connected.set()
    
    def __ws_on_close(self, ws, status, message):
        """Callback method that is envoked when the web socket connection is closed"""
        self.__connected.clear()
    
    @wrap_exception("Error encountered while processing websocket data")
    def __ws_on_message(self, ws, message):
        """Callback method that is envoked when data is received over the web socket connection"""
        LOGGER.debug(f"Recieved: {message}")
        data = json.loads(message)
        if ZONE_DATA in data:
            with self.__locks[ZONE_DATA]:
                #TODO: add this to the model
                self.zones = data[ZONE_DATA]
            self.__trigger_event(ZONE_DATA)
        elif PATTERN_LIST_DATA in data:
            data = data[PATTERN_LIST_DATA]
            with self.__locks[PATTERN_LIST_DATA]:
                self.pattern_files = []
                for p in data:
                    if p["name"] != "":
                        self.pattern_files.append(PatternName(p["folders"], p["name"]))
            self.__trigger_event(PATTERN_LIST_DATA)
        elif RUN_PATTERN_DATA in data:
            data = data[RUN_PATTERN_DATA]
            if len(data["zoneName"]) == 1:
                zone = data["zoneName"][0]
                with self.__locks[RUN_PATTERN_DATA]:
                    self.zone_data[zone] = StateData(**data)
                self.__trigger_event(RUN_PATTERN_DATA, zone)
    
    def __send(self, data: Any):
        """Sends data to the controller over the web socket connection"""
        LOGGER.debug(f"Sending: {message}")
        self.__ws.send(json.dumps(vars(data)))

    @property
    def connected(self) -> bool:
        """Returns true if the the web socket connection to the controller is established"""
        return self.__connected.is_set()

    @wrap_exception("Error encountered while retrieving pattern list")
    def get_pattern_list(self, timeout: Optional[float] = DEFAULT_TIMEOUT) -> List[PatternName]:
        """Returns and stores the list of pre-set patterns from the controller"""
        self.__send(GetDataRequest([PATTERN_LIST_DATA]))
        self.__events[PATTERN_LIST_DATA].wait(timeout)
        with self.__locks[PATTERN_LIST_DATA]:
            return self.patternFiles

    @wrap_exception("Error encountered while retrieving zone list")
    def get_zones(self, timeout: Optional[float] = DEFAULT_TIMEOUT) -> Dict:
        """Returns and stores zones, including their port numbers"""
        self.__send(GetDataRequest([ZONE_DATA]))
        self.__events[ZONE_DATA].wait(timeout)
        with self.__locks[ZONE_DATA]:
            return self.zones

    @wrap_exception("Error encountered while retrieving zone run pattern")
    def get_zone_state(self, zone: str, timeout: Optional[float] = DEFAULT_TIMEOUT) -> StateData:
        """Returns and stores the state of the specified zone"""
        self.__send(GetDataRequest([RUN_PATTERN_DATA, zone]))
        self.__get_run_pattern_event(zone).wait(timeout)
        with self.__locks[RUN_PATTERN_DATA]:
            return self.run_patterns[zone]

    @wrap_exception("Error encountered while retrieving zone run patterns")
    def get_zone_states(self, zones: List[str] = None, timeout: Optional[float] = DEFAULT_TIMEOUT) -> Dict[str, StateData]:
        """Returns and stores the state of specified zones, or all zones if zones is None"""
        zones = zones or list(self.zones.keys())
        for zone in zones:
            self.__send(GetDataRequest([RUN_PATTERN_DATA, zone]))
            self.__get_run_pattern_event(zone).wait(timeout)
        with self.__locks[RUN_PATTERN_DATA]:
            return self.zone_data
    
    def connect(self, timeout: Optional[float] = DEFAULT_TIMEOUT) -> None:
        """Establishes a connection to the JellyFish Lighting controller at the given address and begins listening for messages"""
        try:
            self.__ws = websocket.WebSocketApp(
                f"ws://{self.__address}:9000",
                on_open = self.__ws_on_open,
                on_close = self.__ws_on_close,
                on_message = self.__ws_on_message
            )
            self.__ws_thread = Thread(target=lambda: self.__ws.run_forever(), daemon=True)
            self.__ws_thread.start()
            if not self.__connected.wait(timeout=timeout):
                raise JellyFishLightsException(f"Connection to controller at {self.__address} timed out")
        except JellyFishLightsException:
            raise
        except e:
            raise JellyFishLightsException(f"Could not connect to controller at {self.__address}") from e
    
    # Disconnects the web socket connection
    def disconnect(self, timeout: Optional[float] = DEFAULT_TIMEOUT):
        """Disconnects from the JellyFish Lighting controller"""
        try:
            self.__ws.close()
            self.__ws_thread.join(timeout)
            if self.__ws_thread.is_alive():
                raise JellyFishLightsException(f"Attempt to disconnect from controller at {self.__address} timed out")
        except JellyFishLightsException:
            raise
        except e:
            raise JellyFishLightsException(f"Error encountered while disconnecting from controller at {self.__address}") from e

    def connect_and_get_data(self):
        """Connects to the JellyFish Lighting controller at the given address and retrieves zone and pattern data"""
        self.connect()
        self.getZones()
        self.getPatternList()

    def __turn_on_off(self, turnOn: bool, zones: List[str] = None):
        """Convenience function that turns zones on or off"""
        req = RunPatternRequest(
            state=1 if turnOn else 0,
            zoneName=zones or list(self.zones.keys()))
        self.__send(req)

    @wrap_exception("Error encountered while turning on zone(s)")
    def turn_on(self, zones: List[str] = None):
        """Turns on the provided zone(s) (or all zones if not provided)"""
        self.__turn_on_off(True, zones or list(self.zones.keys()))

    @wrap_exception("Error encountered while turning off zone(s)")
    def turn_off(self, zones: List[str] = None):
        """Turns off the provided zone(s) (or all zones if not provided)"""
        self.turn_on_off(False, zones or list(self.zones.keys()))

    @wrap_exception("Error encountered while applying light string to zone(s)")
    def apply_light_string(self, light_string: List[Tuple[int, int, int]], zones: List[str] = None):
        """Sets lights in the provided zone(s) to a custom string of colors (or all zones if not provided)"""
        #TODO: add brightness control
        colors = [0,0,0]
        colors_pos = [-1]
        for i, rgb in enumerate(light_string):
            assert valid_rgb(rgb)
            colors.extend(rgb)
            colors_pos.append(i)

        rd = RunData(speed=0, brightness=100, effect="No Effect", effect_value=0, rgb_adj=[100,100,100])
        rpd = RunPatternData(colors=colors, color_pos=colors_pos, run_data=rd, type="Soffit")
        
        req = RunPatternRequest(
            state=3,
            zone_name=zones or list(self.zones.keys()),
            data=rpd
        )
        self.__send(req)

    @wrap_exception("Error encountered while applying color to zone(s)")
    def apply_color(self, rgb: Tuple[int,int,int], brightness: int = 100, zones: List[str] = None):
        """Sets all lights in the provided zone(s) to a solid color at the given brightness (or all zones if not provided. Default brighness = 100%)"""
        assert valid_rgb(rgb)
        assert valid_brightness(brightness)
        rd = RunData(speed=10, brightness=brightness, effect="No Effect", effect_value=0, rgb_adj=[100,100,100])
        rpd = RunPatternData(colors=[*rgb], type="Color", skip=1, direction="Left", run_data=rd)
        
        req = RunPatternRequest(
            state=1,
            zone_name=zones or list(self.zones.keys()),
            data=rpd
        )
        self.__send(req)
    
    @wrap_exception("Error encountered while applying pattern to zone(s)")
    def apply_pattern(self, pattern: str, zones: List[str] = None):
        """Activates a predefined pattern on the provided zone(s)"""
        req = RunPatternRequest(
            state=1,
            zoneName=zones or list(self.zones.keys()),
            file=pattern
        )
        self.__send(req)