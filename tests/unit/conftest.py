import pytest
import json
from typing import List
from jellyfishlightspy.helpers import to_json, from_json
from jellyfishlightspy.model import RunData, PatternData, StateData, Pattern, ZoneData, PortMapping
from jellyfishlightspy.requests import GetRequest, SetRequest
from tests.helpers import Helpers

@pytest.fixture
def helpers() -> Helpers:
    return Helpers

@pytest.fixture
def rd_obj() -> RunData:
    return RunData(speed = 20, brightness = 100, effect = "test-effect", effectValue = 1, rgbAdj = [2,3,4])

@pytest.fixture
def rd_json() -> str:
    return '{"speed": 20, "brightness": 100, "effect": "test-effect", "effectValue": 1, "rgbAdj": [2, 3, 4]}'

@pytest.fixture
def rpd_obj(rd_obj) -> PatternData:
    return PatternData(colors = [0,1,2,3,4,5], type = "test-type", runData = rd_obj, direction = "test-direction", spaceBetweenPixels = 5, numOfLeds = 6, skip = 7, effectBetweenPixels = "test-effect-between-pixels", colorPos = [8, 9, 10], cursor = 11)

@pytest.fixture
def rpd_json(rd_json) -> str:
    return '{"colors": [0, 1, 2, 3, 4, 5], "type": "test-type", "runData": ' + rd_json + ', "direction": "test-direction", "spaceBetweenPixels": 5, "numOfLeds": 6, "skip": 7, "effectBetweenPixels": "test-effect-between-pixels", "colorPos": [8, 9, 10], "cursor": 11}'

@pytest.fixture
def sd_obj(rpd_obj) -> StateData:
    return StateData(state = 1, zoneName = ["test-zone-1", "test-zone-2"], file = "test-file", id = "test-id", data = rpd_obj)

@pytest.fixture
def sd_json(rpd_json) -> str:
    escaped = rpd_json.replace('"', '\\"')
    return '{"state": 1, "zoneName": ["test-zone-1", "test-zone-2"], "file": "test-file", "id": "test-id", "data": "' + escaped + '"}'

@pytest.fixture
def pattern_list() -> List[Pattern]:
    return [
        Pattern("test-folder-1", "", False),
        Pattern("test-folder-1", "test-name-1", True),
        Pattern("test-folder-2", "", False),
        Pattern("test-folder-2", "test-name-1", True),
        Pattern("test-folder-2", "test-name-2", True),
    ]

@pytest.fixture
def pattern_json() -> str:
    return '[{"folders":"test-folder-1","name":"","readOnly":false},{"folders":"test-folder-1","name":"test-name-1","readOnly":true},{"folders":"test-folder-2","name":"","readOnly":false},{"folders":"test-folder-2","name":"test-name-1","readOnly":true},{"folders":"test-folder-2","name":"test-name-2","readOnly":true}]'

@pytest.fixture
def gd_req_obj() -> GetRequest:
    return GetRequest("zones")

@pytest.fixture
def gd_req_json() -> str:
    return '{"cmd": "toCtlrGet", "get": [["zones"]]}'

@pytest.fixture
def rp_req_obj(rpd_obj) -> SetRequest:
    return SetRequest(1, ["test-zone-1", "test-zone-2"], file = "test-folder/test-name", id = "test-id", data = rpd_obj)

@pytest.fixture
def rp_req_json(rpd_json) -> str:
    escaped = rpd_json.replace('"', '\\"')
    return '{"cmd": "toCtlrSet", "runPattern": {"state": 1, "zoneName": ["test-zone-1", "test-zone-2"], "file": "test-folder/test-name", "id": "test-id", "data": "' + escaped + '"}}'

@pytest.fixture
def zc_obj() -> ZoneData:
    return ZoneData(26, [PortMapping("test-ctlr", 1, 2, 3, 4),PortMapping("test-ctlr", 5, 6, 7, 8)])

@pytest.fixture
def zc_json() -> str:
    return '{"numPixels":26,"portMap":[{"ctlrName":"test-ctlr","phyEndIdx":1,"phyPort":2,"phyStartIdx":3,"zoneRGBStartIdx":4}, {"ctlrName":"test-ctlr","phyEndIdx":5,"phyPort":6,"phyStartIdx":7,"zoneRGBStartIdx":8}]}'

@pytest.fixture
def patterns_repsonse_json(pattern_json) -> str:
    return '{"cmd":"fromCtlr","patternFileList":' + pattern_json + '}'

@pytest.fixture
def zones_repsonse_json() -> str:
    return '{"cmd":"fromCtlr","save":true,"zones":{"test-zone-1":{"numPixels":26,"portMap":[{"ctlrName":"JellyFish.local","phyEndIdx":64,"phyPort":1,"phyStartIdx":89,"zoneRGBStartIdx":0}]},"test-zone-2":{"numPixels":64,"portMap":[{"ctlrName":"JellyFish.local","phyEndIdx":63,"phyPort":1,"phyStartIdx":0,"zoneRGBStartIdx":0}]}}}'

@pytest.fixture
def zone_state_repsonse_json() -> str:
    return '{"cmd":"fromCtlr","runPattern":{"data":"","file":"Accent/Custom Front","id":"Front","state":0,"zoneName":["Front"]}}'