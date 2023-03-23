from typing import Optional, List, Dict

class ModelBase():
    def __repr__(self) -> str:
        return self.__class__.__name__ + str(vars(self))


class ControllerVersion(ModelBase):
    def __init__(self, ver: str, details: str, isUpdate: bool):
        self.ver = ver
        self.details = details
        self.isUpdate = isUpdate


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
    def __init__(self, speed: int=0, brightness: int=100, effect: str="No Effect", effectValue: int=0, rgbAdj: List[int]=[100, 100, 100]) -> None:
        self.speed = speed
        self.brightness = brightness
        self.effect = effect
        self.effectValue = effectValue
        self.rgbAdj = rgbAdj


class Pattern(ModelBase):
    def __init__(self, folders: str, name: str, readOnly: Optional[bool]=False):
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


class PatternConfig(ModelBase):
    def __init__(self, type: str, colors: List[int], runData: RunConfig=None, direction: str="Center", spaceBetweenPixels: int=2, numOfLeds: int=1, skip: int=2, effectBetweenPixels: str="No Color Transform", colorPos: List[int]=[-1], cursor: int=-1, ledOnPos: Dict[str, int]={}, soffitZone: str="") -> None:
        self.type = type
        self.colors = colors
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


class ZoneState(ModelBase):
    def __init__(self, state: int, zoneName: List[str], file: Optional[str]=None, id: Optional[str]=None, data: Optional[PatternConfig]=None):
        self.state = state
        self.zoneName = zoneName
        self.file = file
        self.id = id
        self.data = data

    @property
    def is_on(self) -> bool:
        return self.state != 0


class ScheduleEventAction(ModelBase):
    def __init__(self, type: str, startFrom: str, hour: int, minute: int, patternFile: str, zones: List[str]):
        self.type = type
        self.startFrom = startFrom
        self.hour = hour
        self.minute = minute
        self.patternFile = patternFile if type == "RUN" else ""
        self.zones = zones


class ScheduleEvent(ModelBase):
    def __init__(self, days: List[str], actions: List[ScheduleEventAction], label: Optional[str] = ""):
        self.label = label
        self.days = days
        self.actions = actions