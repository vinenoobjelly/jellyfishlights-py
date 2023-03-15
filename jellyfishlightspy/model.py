from typing import Optional, List

class PortMapping():
    def __init__(self, ctlrName: str, phyEndIdx: int, phyPort: int, phyStartIdx: int, zoneRGBStartIdx: int):
        self.ctlrName = ctlrName
        self.phyEndIdx = phyEndIdx
        self.phyPort = phyPort
        self.phyStartIdx = phyStartIdx
        self.zoneRGBStartIdx = zoneRGBStartIdx

class ZoneData():
    def __init__(self, numPixels: int, portMap: List[PortMapping]):
        self.numPixels = numPixels
        self.portMap = portMap

class RunData():
    def __init__(self, speed: Optional[int], brightness: Optional[int], effect: Optional[str], effectValue: Optional[int], rgbAdj: Optional[List[int]]) -> None:
        self.speed = speed
        self.brightness = brightness
        self.effect = effect
        self.effectValue = effectValue
        self.rgbAdj = rgbAdj

class PatternData():
    def __init__(self, colors: List[int], type: str, runData: RunData, direction: str = "Center", spaceBetweenPixels: int = 2, numOfLeds: int = 1, skip: int = 2, effectBetweenPixels: str = "No Color Transform", colorPos: List[int] = [-1], cursor: int = -1) -> None:
        self.colors = colors
        self.type = type
        self.runData = runData
        self.direction = direction
        self.spaceBetweenPixels = spaceBetweenPixels
        self.numOfLeds = numOfLeds
        self.skip = skip
        self.effectBetweenPixels = effectBetweenPixels
        self.colorPos = colorPos
        self.cursor = cursor

class StateData():
    def __init__(self, state: int, zoneName: List[str], file: Optional[str] = None, id: Optional[str] = None, data: Optional[PatternData] = None):
        self.state = state
        self.zoneName = zoneName
        self.file = file
        self.id = id
        self.data = data

    @property
    def is_on(self) -> bool:
        # TODO: Figure out what -1 means to validate this logic
        return self.state != 0

class Pattern:
    folders: str
    name: str

    def __init__(self, folders: str, name: str, readOnly: bool):
        self.folders = folders
        self.name = name
        self.readOnly = readOnly

    def __str__(self) -> str:
        return f'{self.folders}/{self.name}'