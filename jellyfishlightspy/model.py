from typing import Optional, List

class RunData:

    def __init__(self, speed: Optional[int], brightness: Optional[int], effect: Optional[str], effectValue: Optional[int], rgbAdj: Optional[List[int]]) -> None:
        self.speed = speed
        self.brightness = brightness
        self.effect = effect
        self.effectValue = effectValue
        self.rgbAdj = rgbAdj


class RunPatternData:

    def __init__(self, colors: List[int], type: str, runData: RunData, direction: str = "Center", spaceBetweenPixels: int = 2, numOfLeds: int = 1, skip: int = 2, effectBetweenPixels: str = "No Color Transform", colorPos: List[int] = [-1], cursor: int = -1) -> None:
        self.colors = colors
        self.spaceBetweenPixels = spaceBetweenPixels
        self.effectBetweenPixels = effectBetweenPixels
        self.colorPos = colorPos
        self.cursor = cursor
        self.type = type
        self.skip = skip
        self.numOfLeds = numOfLeds
        self.runData = runData
        self.direction = direction


class StateData:
    
    def __init__(self, state: int, zoneName: List[str], file: str = "", id: str = "", data: Optional[RunPatternData] = None):
        self.state = state
        self.zoneName = zoneName
        self.file = file
        self.id = id
        self.data = data


class PatternName:
    folder: str
    name: str

    def __init__(self, folder: str, name: str):
        self.folder = folder
        self.name = name

    def __str__(self) -> str:
        return f'{self.folder}/{self.name}'