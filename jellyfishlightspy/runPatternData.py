# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = RunPatternDatafromdict(json.loads(json_string))

from typing import Optional, List, Any, TypeVar, Callable, Type, cast


T = TypeVar("T")


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


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
    speed: Optional[int]
    brightness: Optional[int]
    effect: Optional[str]
    effectValue: Optional[int]
    rgbAdj: Optional[List[int]]

    def __init__(self, speed: Optional[int], brightness: Optional[int], effect: Optional[str], effectValue: Optional[int], rgbAdj: Optional[List[int]]) -> None:
        self.speed = speed
        self.brightness = brightness
        self.effect = effect
        self.effectValue = effectValue
        self.rgbAdj = rgbAdj

    @staticmethod
    def from_dict(obj: Any) -> 'RunData':
        assert isinstance(obj, dict)
        speed = from_union([from_int, from_none], obj.get("speed"))
        brightness = from_union([from_int, from_none], obj.get("brightness"))
        effect = from_union([from_str, from_none], obj.get("effect"))
        effectValue = from_union([from_int, from_none], obj.get("effectValue"))
        rgbAdj = from_union([lambda x: from_list(from_int, x), from_none], obj.get("rgbAdj"))
        return RunData(speed, brightness, effect, effectValue, rgbAdj)

    def to_dict(self) -> dict:
        result: dict = {}
        result["speed"] = from_union([from_int, from_none], self.speed)
        result["brightness"] = from_union([from_int, from_none], self.brightness)
        result["effect"] = from_union([from_str, from_none], self.effect)
        result["effectValue"] = from_union([from_int, from_none], self.effectValue)
        result["rgbAdj"] = from_union([lambda x: from_list(from_int, x), from_none], self.rgbAdj)
        return result


class RunPatternData:
    colors: Optional[List[int]]
    spaceBetweenPixels: Optional[int]
    effectBetweenPixels: Optional[str]
    colorPos: Optional[List[int]]
    cursor: Optional[int]
    type: Optional[str]
    skip: Optional[int]
    numOfLeds: Optional[int]
    runData: Optional[RunData]
    direction: Optional[str]

    #Note: When this was pasted for optional params, all of the parameters were surrounded in Optional[param]
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
        colors = from_union([lambda x: from_list(from_int, x), from_none], obj.get("colors"))
        spaceBetweenPixels = from_union([from_int, from_none], obj.get("spaceBetweenPixels"))
        effectBetweenPixels = from_union([from_str, from_none], obj.get("effectBetweenPixels"))
        colorPos = from_union([lambda x: from_list(from_int, x), from_none], obj.get("colorPos"))
        cursor = from_union([from_int, from_none], obj.get("cursor"))
        type = from_union([from_str, from_none], obj.get("type"))
        skip = from_union([from_int, from_none], obj.get("skip"))
        numOfLeds = from_union([from_int, from_none], obj.get("numOfLeds"))
        runData = from_union([RunData.from_dict, from_none], obj.get("runData"))
        direction = from_union([from_str, from_none], obj.get("direction"))
        return RunPatternData(colors, spaceBetweenPixels, effectBetweenPixels, colorPos, cursor, type, skip, numOfLeds, runData, direction)

    def to_dict(self) -> dict:
        result: dict = {}
        result["colors"] = from_union([lambda x: from_list(from_int, x), from_none], self.colors)
        result["spaceBetweenPixels"] = from_union([from_int, from_none], self.spaceBetweenPixels)
        result["effectBetweenPixels"] = from_union([from_str, from_none], self.effectBetweenPixels)
        result["colorPos"] = from_union([lambda x: from_list(from_int, x), from_none], self.colorPos)
        result["cursor"] = from_union([from_int, from_none], self.cursor)
        result["type"] = from_union([from_str, from_none], self.type)
        result["skip"] = from_union([from_int, from_none], self.skip)
        result["numOfLeds"] = from_union([from_int, from_none], self.numOfLeds)
        result["runData"] = from_union([lambda x: to_class(RunData, x), from_none], self.runData)
        result["direction"] = from_union([from_str, from_none], self.direction)
        return result


def RunPatternDatafromdict(s: Any) -> RunPatternData:
    return RunPatternData.from_dict(s)


def RunPatternDatatodict(x: RunPatternData) -> Any:
    return to_class(RunPatternData, x)
