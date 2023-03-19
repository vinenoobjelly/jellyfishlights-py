from typing import Optional, List, Dict

class ModelBase():
    def __repr__(self) -> str:
        return str(vars(self))

class PortMapping(ModelBase):
    def __init__(self, ctlrName: str, phyEndIdx: int, phyPort: int, phyStartIdx: int, zoneRGBStartIdx: int):
        self.ctlrName = ctlrName
        self.phyEndIdx = phyEndIdx
        self.phyPort = phyPort
        self.phyStartIdx = phyStartIdx
        self.zoneRGBStartIdx = zoneRGBStartIdx

class ZoneConfig(ModelBase):
    def __init__(self, numPixels: int, portMap: List[PortMapping]):
        self.numPixels = numPixels
        self.portMap = portMap

class RunConfig(ModelBase):
    def __init__(self, speed: Optional[int], brightness: Optional[int], effect: Optional[str], effectValue: Optional[int], rgbAdj: Optional[List[int]]) -> None:
        self.speed = speed
        self.brightness = brightness
        self.effect = effect
        self.effectValue = effectValue
        self.rgbAdj = rgbAdj

class PatternConfig(ModelBase):
    def __init__(self, colors: List[int], type: str, runData: RunConfig, direction: str = "Center", spaceBetweenPixels: int = 2, numOfLeds: int = 1, skip: int = 2, effectBetweenPixels: str = "No Color Transform", colorPos: List[int] = [-1], cursor: int = -1, ledOnPos: Dict[str, int] = {}, soffitZone: str = "") -> None:
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
        # These attributes appear to be optional and are only seen on soffit patterns
        self.ledOnPos = ledOnPos
        self.soffitZone = soffitZone

class State(ModelBase):
    def __init__(self, state: int, zoneName: List[str], file: Optional[str] = None, id: Optional[str] = None, data: Optional[PatternConfig] = None):
        self.state = state
        self.zoneName = zoneName
        self.file = file
        self.id = id
        self.data = data

    @property
    def is_on(self) -> bool:
        # TODO: Figure out what -1 means to validate this logic
        return self.state != 0

class Pattern(ModelBase):
    def __init__(self, folders: str, name: str, readOnly: Optional[bool] = False):
        self.folders = folders
        self.name = name
        self.readOnly = readOnly

    @property
    def is_folder(self) -> bool:
        return not bool(self.name)

    def __repr__(self) -> str:
        return f'{self.folders}/{self.name}'

    @classmethod
    def from_str(cls, pattern_name: str):
        folders, delim, name = pattern_name.rpartition("/")
        return cls(folders, name)