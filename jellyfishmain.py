# https://medium.com/@joel.barmettler/how-to-upload-your-python-package-to-pypi-65edc5fe9c56
#TODO: get rid of above once this is done

from logging import fatal
from typing import Dict
import websocket
import json
from runPattern import RunPatternClass, RunPattern
from runPatternData import RunData, RunPatternData
from getData import GetData
from typing import List
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
        return self.folder + "/" + self.name

#TODO: adding and setting patterns, schedules, and zones
#TODO: get current schedule
#TODO: add a way to get the current pattern (runPattern)
#TODO: add use of prebuilt pattern types
class JellyFishController:
    zones: Dict = {}
    patternFiles: List[PatternName] = []
    __ws = websocket.WebSocket()
    __address: str
    __printJSON: bool

    def __init__(self, address: str, printJSON: bool = False):
        self.__address = address
        self.__printJSON = printJSON
    
    def __send(self, message: str):
        if self.__printJSON:
            print("Sending: " + message)
        self.__ws.send(message)

    def __recv(self):
        message = self.__ws.recv()
        if self.__printJSON:
            print("Recieved: " + message)
        return message

    def getPatterns(self) -> List[PatternName]:
        """Returns and stores all the patterns from the controller"""
        patternFiles = self.__getData("patternFileList")
        for patternFile in patternFiles:
            if patternFile["name"] != "":
                self.patternFiles.append(PatternName(patternFile["name"], patternFile["folders"]))
        return self.patternFiles

    def getZones(self) -> Dict:
        """Returns and stores zones, including their port numbers"""
        zones = self.__getData("zones")
        self.zones = zones
        return self.zones

    def __getData(self, data) -> any:
        gd = GetData(cmd='toCtlrGet', get=[[data]])
        self.__send(json.dumps(gd.to_dict()))
        return json.loads(self.__recv())[data]

    #Attempts to connect to a controller at the givin address
    def connectAndGetData(self):
        try:
            self.__ws.connect("ws://" + self.__address + ":9000")
            self.getZones()
            self.getPatterns()
        except:
            print("Could not connect to controller at " + self.__address)
        

    def playPattern(self, pattern: str, zones: List[str] = None):
        rpc = RunPatternClass(state=1, zoneName=list(self.zones.keys()) if not zones else zones, file=pattern, data="")
        rp = RunPattern(cmd="toCtlrSet", runPattern=rpc)
        self.__send(json.dumps(rp.to_dict()))

    def turnOnOff(self, turnOn: bool, zones: List[str] = None):
        rpc = RunPatternClass(state=1 if turnOn else 0, zoneName=list(self.zones.keys()) if not zones else zones, data="")
        rp = RunPattern(cmd="toCtlrSet", runPattern=rpc)
        self.__send(json.dumps(rp.to_dict()))

    def turnOn(self, zones: List[str] = None):
        self.turnOnOff(True, list(self.zones.keys()) if not zones else zones)

    def turnOff(self, zones: List[str] = None):
        self.turnOnOff(False, list(self.zones.keys()) if not zones else zones)

    def sendLightString(self, lightString: LightString, zones: List[str] = None):
        colors = [0,0,0]
        colorsPos = [-1]
        for i, light in enumerate(lightString.lights):
            colors.append(light.red)
            colors.append(light.green)
            colors.append(light.blue)
            colorsPos.append(i)
            
        rd = RunData(speed=0, brightness=100, effect="No Effect", effectValue=0, rgbAdj=[100,100,100])
        rpd = RunPatternData(colors=colors, colorPos=colorsPos, runData=rd, type="Soffit")
        rpc = RunPatternClass(state=3, zoneName=list(self.zones.keys()) if not zones else zones, data= json.dumps(rpd.to_dict()))
        rp = RunPattern(cmd="toCtlrSet", runPattern=rpc)
        self.__send(json.dumps(rp.to_dict()))
