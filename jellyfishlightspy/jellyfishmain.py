# https://medium.com/@joel.barmettler/how-to-upload-your-python-package-to-pypi-65edc5fe9c56
#TODO: get rid of above once this is done

import websocket
import json
import traceback
from typing import Dict, List, Tuple
from threading import Thread, Event, Lock
from jellyfishlightspy.runPattern import *
from jellyfishlightspy.runPatternData import *
from jellyfishlightspy.getData import *
from dataclasses import dataclass

class Light:
    """Represents a single light on an Led strip"""
    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue

#Do we NEED a wrapper for a List[Light]?
class LightString:
    """Represents a series of Lights on an led strip"""
    lights: List[Light]
    def __init__(self, lightz: List[Light] = None):
        self.lights = [] if lightz is None else lightz

    def add(self, light: Light):
        self.lights.append(light)

@dataclass
class PatternName:
    name: str
    folder: str

    def toFolderAndName(self):
        return f'{self.folder}/{self.name}'

#TODO: adding and setting patterns, schedules, and zones
#TODO: get current schedule
#TODO: add a way to get the current pattern (runPattern)
#TODO: add use of prebuilt pattern types

ZONE_DATA = "zones"
PATTERN_LIST_DATA = "patternFileList"
RUN_PATTERN_DATA = "runPattern"

class JellyFishController:

    def __init__(self, address: str, printJSON: bool = False):
        self.zones: Dict = {}
        self.patternFiles: List[PatternName] = []
        self.runPatterns: Dict = {}
        self.__ws: websocket.WebSocketApp = None
        self.__wsThread: Thread = None
        self.__connected: Event = Event()
        self.__address = address
        self.__printJSON = printJSON
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
    
    def __getRunPatternEvent(self, zone: str) -> Event:
        if zone not in self.__events[RUN_PATTERN_DATA]:
            self.__events[RUN_PATTERN_DATA][zone] = Event()
        return self.__events[RUN_PATTERN_DATA][zone]
    
    def __triggerEvent(self, dataKey, zone = None):
        event = self.__events[dataKey] if zone is None else self.__getRunPatternEvent(zone)
        event.set()
        event.clear()
    
    def __ws_on_open(self, ws):
        self.__connected.set()
    
    def __ws_on_close(self, ws, status, message):
        self.__connected.clear()
    
    def __ws_on_message(self, ws, message):
        try:
            if self.__printJSON:
                print(f"Recieved: {message}")
            data = json.loads(message)
            if ZONE_DATA in data:
                with self.__locks[ZONE_DATA]:
                    self.zones = data[ZONE_DATA]
                self.__triggerEvent(ZONE_DATA)
            elif PATTERN_LIST_DATA in data:
                data = data[PATTERN_LIST_DATA]
                with self.__locks[PATTERN_LIST_DATA]:
                    self.patternFiles = []
                    for patternFile in data:
                        if patternFile["name"] != "":
                            self.patternFiles.append(PatternName(patternFile["name"], patternFile["folders"]))
                self.__triggerEvent(PATTERN_LIST_DATA)
            elif RUN_PATTERN_DATA in data:
                data = data[RUN_PATTERN_DATA]
                if len(data["zoneName"]) == 1:
                    zone = data["zoneName"][0]
                    with self.__locks[RUN_PATTERN_DATA]:
                        self.runPatterns[zone] = RunPatternClassFromDict(data)
                    self.__triggerEvent(RUN_PATTERN_DATA, zone)
        except:
            print("Error encountered while processing websocket data!")
            traceback.print_exc()
    
    def __send(self, message: str):
        if self.__printJSON:
            print(f"Sending: {message}")
        self.__ws.send(message)

    def __requestData(self, data: List[str]):
        gd = GetData(cmd='toCtlrGet', get=[data])
        self.__send(json.dumps(gd.to_dict()))
    
    @property
    def connected(self) -> bool:
        return self.__connected.is_set()

    def getPatternList(self, timeout = None) -> List[PatternName]:
        """Returns and stores all the patterns from the controller"""
        self.__requestData([PATTERN_LIST_DATA])
        self.__events[PATTERN_LIST_DATA].wait(timeout)
        with self.__locks[PATTERN_LIST_DATA]:
            return self.patternFiles

    def getZones(self, timeout = None) -> Dict:
        """Returns and stores zones, including their port numbers"""
        self.__requestData([ZONE_DATA])
        self.__events[ZONE_DATA].wait(timeout)
        with self.__locks[ZONE_DATA]:
            return self.zones

    def getRunPattern(self, zone: str, timeout = None) -> RunPatternClass:
        """Returns and stores the state of the specified zone"""
        self.__requestData([RUN_PATTERN_DATA, zone])
        self.__getRunPatternEvent(zone).wait(timeout)
        with self.__locks[RUN_PATTERN_DATA]:
            return self.runPatterns[zone]

    def getRunPatterns(self, zones: List[str] = None, timeout = None) -> Dict[str, RunPatternClass]:
        """Returns and stores the state of specified zones"""
        zones = zones or list(self.zones.keys())
        for zone in zones:
            self.__requestData([RUN_PATTERN_DATA, zone])
            self.__getRunPatternEvent(zone).wait(timeout)
        with self.__locks[RUN_PATTERN_DATA]:
            return self.runPatterns
    
    #Attempts to connect to a controller at the given address
    def connect(self):
        try:
            self.__ws = websocket.WebSocketApp(
                f"ws://{self.__address}:9000",
                on_open = self.__ws_on_open,
                on_close = self.__ws_on_close,
                on_message = self.__ws_on_message
            )
            self.__wsThread = Thread(target=lambda: self.__ws.run_forever(), daemon=True)
            self.__wsThread.start()
            self.__connected.wait()
        except Exception as e:
            raise BaseException(f"Could not connect to controller at {self.__address}", e)
    
    # Disconnects the web socket connection
    def disconnect(self):
        try:
            self.__ws.close()
            self.__wsThread.join()
        except Exception as e:
            raise BaseException(f"Error encountered while disconnecting from controller at {self.__address}", e)

    #Attempts to connect to a controller at the given address and retrieve data
    def connectAndGetData(self):
        try:
            self.connect()
            self.getZones()
            self.getPatternList()
        except Exception as e:
            raise BaseException("Error connecting or getting data: ", e)
        
    def playPattern(self, pattern: str, zones: List[str] = None):
        rpc = RunPatternClass(
            state=1,
            zoneName=zones or list(self.zones.keys()),
            file=pattern,
            data="",
        )

        rp = RunPattern(cmd="toCtlrSet", runPattern=rpc)
        self.__send(json.dumps(rp.to_dict()))

    def turnOnOff(self, turnOn: bool, zones: List[str] = None):
        zones = zones or list(self.zones.keys())
        rpc = RunPatternClass(
            state=1 if turnOn else 0,
            zoneName=zones,
            data="",
        )

        rp = RunPattern(cmd="toCtlrSet", runPattern=rpc)
        self.__send(json.dumps(rp.to_dict()))

    def turnOn(self, zones: List[str] = None):
        self.turnOnOff(True, zones or list(self.zones.keys()))

    def turnOff(self, zones: List[str] = None):
        self.turnOnOff(False, zones or list(self.zones.keys()))

    def sendLightString(self, lightString: LightString, zones: List[str] = None):
        colors = [0,0,0]
        colorsPos = [-1]
        for i, light in enumerate(lightString.lights):
            colors.extend((light.red, light.green, light.blue))
            colorsPos.append(i)

        rd = RunData(speed=0, brightness=100, effect="No Effect", effectValue=0, rgbAdj=[100,100,100])
        rpd = RunPatternData(colors=colors, colorPos=colorsPos, runData=rd, type="Soffit")
        rpc = RunPatternClass(
            state=3,
            zoneName=zones or list(self.zones.keys()),
            data=json.dumps(rpd.to_dict()),
        )

        rp = RunPattern(cmd="toCtlrSet", runPattern=rpc)
        self.__send(json.dumps(rp.to_dict()))

    def sendColor(self, rgb: Tuple[int,int,int], brightness: int = 100, zones: List[str] = None):
        rd = RunData(speed=10, brightness=brightness, effect="No Effect", effectValue=0, rgbAdj=[100,100,100])
        rpd = RunPatternData(colors=[*rgb], type="Color", skip=1, direction="Left", runData=rd)
        rpc = RunPatternClass(
            state=1,
            zoneName=zones or list(self.zones.keys()),
            data=json.dumps(rpd.to_dict()),
        )
        
        rp = RunPattern(cmd="toCtlrSet", runPattern=rpc)
        self.__send(json.dumps(rp.to_dict()))