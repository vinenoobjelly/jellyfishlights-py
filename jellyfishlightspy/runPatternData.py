# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = RunPatternDatafromdict(json.loads(json_string))

from typing import List, Any, TypeVar, Callable, Type, cast


T = TypeVar("T")


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class RunData:
    speed: int
    brightness: int
    effect: str
    effectValue: int
    rgbAdj: List[int]

    def __init__(self, speed: int, brightness: int, effect: str, effectValue: int, rgbAdj: List[int]) -> None:
        self.speed = speed
        self.brightness = brightness
        self.effect = effect
        self.effectValue = effectValue
        self.rgbAdj = rgbAdj

    @staticmethod
    def from_dict(obj: Any) -> 'RunData':
        assert isinstance(obj, dict)
        speed = from_int(obj.get("speed"))
        brightness = from_int(obj.get("brightness"))
        effect = from_str(obj.get("effect"))
        effectValue = from_int(obj.get("effectValue"))
        rgbAdj = from_list(from_int, obj.get("rgbAdj"))
        return RunData(speed, brightness, effect, effectValue, rgbAdj)

    def to_dict(self) -> dict:
        result: dict = {}
        result["speed"] = from_int(self.speed)
        result["brightness"] = from_int(self.brightness)
        result["effect"] = from_str(self.effect)
        result["effectValue"] = from_int(self.effectValue)
        result["rgbAdj"] = from_list(from_int, self.rgbAdj)
        return result


class RunPatternData:
    colors: List[int]
    spaceBetweenPixels: int
    effectBetweenPixels: str
    colorPos: List[int]
    cursor: int
    type: str
    skip: int
    numOfLeds: int
    runData: RunData
    direction: str

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

    @staticmethod
    def from_dict(obj: Any) -> 'RunPatternData':
        assert isinstance(obj, dict)
        colors = from_list(from_int, obj.get("colors"))
        spaceBetweenPixels = from_int(obj.get("spaceBetweenPixels"))
        effectBetweenPixels = from_str(obj.get("effectBetweenPixels"))
        colorPos = from_list(from_int, obj.get("colorPos"))
        cursor = from_int(obj.get("cursor"))
        type = from_str(obj.get("type"))
        skip = from_int(obj.get("skip"))
        numOfLeds = from_int(obj.get("numOfLeds"))
        runData = RunData.from_dict(obj.get("runData"))
        direction = from_str(obj.get("direction"))
        return RunPatternData(colors, spaceBetweenPixels, effectBetweenPixels, colorPos, cursor, type, skip, numOfLeds, runData, direction)

    def to_dict(self) -> dict:
        result: dict = {}
        result["colors"] = from_list(from_int, self.colors)
        result["spaceBetweenPixels"] = from_int(self.spaceBetweenPixels)
        result["effectBetweenPixels"] = from_str(self.effectBetweenPixels)
        result["colorPos"] = from_list(from_int, self.colorPos)
        result["cursor"] = from_int(self.cursor)
        result["type"] = from_str(self.type)
        result["skip"] = from_int(self.skip)
        result["numOfLeds"] = from_int(self.numOfLeds)
        result["runData"] = to_class(RunData, self.runData)
        result["direction"] = from_str(self.direction)
        return result


def RunPatternDatafromdict(s: Any) -> RunPatternData:
    return RunPatternData.from_dict(s)


def RunPatternDatatodict(x: RunPatternData) -> Any:
    return to_class(RunPatternData, x)
