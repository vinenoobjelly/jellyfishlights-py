# https://medium.com/@joel.barmettler/how-to-upload-your-python-package-to-pypi-65edc5fe9c56
#TODO: get rid of above once this is done

import websocket
import json
import queue
from typing import Dict, List, Tuple
from threading import Thread, Event
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
class JellyFishController:

    def __init__(self, address: str, printJSON: bool = False):
        self.zones: Dict = {}
        self.patternFiles: List[PatternName] = []
        self.__ws: websocket.WebSocketApp = None
        self.__wsThread: Thread = None
        self.__messageQueue = queue.Queue()
        self.__connected: Event = Event()
        self.__address = address
        self.__printJSON = printJSON
    
    def __ws_on_open(self, ws):
        self.__connected.set()
    
    def __ws_on_close(self, ws, status, message):
        self.__connected.clear()
    
    def __ws_on_message(self, ws, message):
        if self.__printJSON:
            print(f"Recieved: {message}")
        self.__messageQueue.put(message)
    
    def __send(self, message: str):
        if self.__printJSON:
            print(f"Sending: {message}")
        self.__ws.send(message)
    
    def __recv(self):
        return self.__messageQueue.get()
    
    def __drain_queue(self):
        # Wait for at least one message to appear in queue
        self.__messageQueue.get()
        # Then read the rest
        # Note: there's an inherent race condition here that can't be avoided...
        #       We may read from the queue faster than messages are received.
        #       This will still exist even with a timeout due to variable network latency
        try:
            while True:
                self.__messageQueue.get(timeout=.1)
        except queue.Empty:
            pass
    
    @property
    def connected(self) -> bool:
        return self.__connected.is_set()

    def getAndStorePatterns(self) -> List[PatternName]:
        """Returns and stores all the patterns from the controller"""
        patternFiles = self.__getData(["patternFileList"])
        for patternFile in patternFiles:
            if patternFile["name"] != "":
                self.patternFiles.append(PatternName(patternFile["name"], patternFile["folders"]))
        return self.patternFiles

    def getAndStoreZones(self) -> Dict:
        """Returns and stores zones, including their port numbers"""
        zones = self.__getData(["zones"])
        self.zones = zones
        return self.zones

    def getRunPattern(self, zone: str=None) -> RunPatternClass:
        """Returns runPatternClass"""
        if not zone:
            zone = list(self.zones.keys())[0]
        runPatterns = self.__getData(["runPattern", zone])
        runPatternsClass = RunPatternClassFromDict(runPatterns)
        return runPatternsClass

    def getRunPatterns(self, zones: List[str]=None) -> Dict[str, RunPatternClass]:
        if not zones:
            zones = list(self.zones.keys())
        runPatterns = {}
        for zone in zones:
            runPatterns[zone] = self.getRunPattern(zone)
        return runPatterns

    def __getData(self, data: List[str]) -> any:
        gd = GetData(cmd='toCtlrGet', get=[data])
        self.__send(json.dumps(gd.to_dict()))
        return json.loads(self.__recv())[data[0]]
    
    #Attempts to connect to a controller at the given address
    def connect(self):
        try:
            self.__ws = websocket.WebSocketApp(
                f"ws://{self.__address}:9000",
                on_open = self.__ws_on_open,
                on_close = self.__ws_on_close,
                on_message = self.__ws_on_message
            )
            self.__wsThread = Thread(target=lambda: self.__ws.run_forever())
            self.__wsThread.start()
            self.__connected.wait()
        except:
            raise BaseException("Could not connect to controller at " + self.__address)
    
    # Disconnects the web socket connection
    def disconnect(self):
        try:
            self.__ws.close()
            self.__wsThread.join()
        except:
            raise BaseException("Error encountered while disconnecting from controller at " + self.__address)

    #Attempts to connect to a controller at the given address and retrieve data
    def connectAndGetData(self):
        try:
            self.connect()
            self.getAndStoreZones()
            self.getAndStorePatterns()
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
        self.__drain_queue()

    def turnOnOff(self, turnOn: bool, zones: List[str] = None):
        zones = zones or list(self.zones.keys())
        rpc = RunPatternClass(
            state=1 if turnOn else 0,
            zoneName=zones,
            data="",
        )

        rp = RunPattern(cmd="toCtlrSet", runPattern=rpc)
        self.__send(json.dumps(rp.to_dict()))
        self.__drain_queue()

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
        self.__drain_queue()

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
        self.__drain_queue()