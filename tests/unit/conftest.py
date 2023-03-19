import pytest
import json
from typing import List
from jellyfishlightspy.helpers import to_json, from_json
from jellyfishlightspy.model import RunConfig, PatternConfig, State, Pattern, ZoneConfig, PortMapping
from jellyfishlightspy.requests import GetRequest, SetStateRequest, SetPatternConfigRequest
from tests.helpers import Helpers

@pytest.fixture
def helpers() -> Helpers:
    return Helpers

@pytest.fixture
def rc_obj() -> RunConfig:
    return RunConfig(speed = 20, brightness = 100, effect = "test-effect", effectValue = 1, rgbAdj = [2,3,4])

@pytest.fixture
def rc_json() -> str:
    return '{"speed": 20, "brightness": 100, "effect": "test-effect", "effectValue": 1, "rgbAdj": [2, 3, 4]}'

@pytest.fixture
def pc_obj(rc_obj) -> PatternConfig:
    return PatternConfig(colors = [0,1,2,3,4,5], type = "test-type", runData = rc_obj, direction = "test-direction", spaceBetweenPixels = 5, numOfLeds = 6, skip = 7, effectBetweenPixels = "test-effect-between-pixels", colorPos = [8, 9, 10], cursor = 11, ledOnPos = {"0": [], "1": [1]}, soffitZone = "test-zone-1")

@pytest.fixture
def pc_json(rc_json) -> str:
    return '{"colors": [0, 1, 2, 3, 4, 5], "type": "test-type", "runData": ' + rc_json + ', "direction": "test-direction", "spaceBetweenPixels": 5, "numOfLeds": 6, "skip": 7, "effectBetweenPixels": "test-effect-between-pixels", "colorPos": [8, 9, 10], "cursor": 11, "ledOnPos": {"0": [], "1": [1]}, "soffitZone": "test-zone-1"}'

@pytest.fixture
def s_obj(pc_obj) -> State:
    return State(state = 1, zoneName = ["test-zone-1", "test-zone-2"], file = "test-file", id = "test-id", data = pc_obj)

@pytest.fixture
def s_json(pc_json) -> str:
    escaped = pc_json.replace('"', '\\"')
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
def get_req_obj() -> GetRequest:
    return GetRequest("zones")

@pytest.fixture
def get_req_json() -> str:
    return '{"cmd": "toCtlrGet", "get": [["zones"]]}'

@pytest.fixture
def set_state_req_obj(pc_obj) -> SetStateRequest:
    return SetStateRequest(1, ["test-zone-1", "test-zone-2"], file = "test-folder/test-name", id = "test-id", data = pc_obj)

@pytest.fixture
def set_state_req_json(pc_json) -> str:
    escaped = pc_json.replace('"', '\\"')
    return '{"cmd": "toCtlrSet", "runPattern": {"state": 1, "zoneName": ["test-zone-1", "test-zone-2"], "file": "test-folder/test-name", "id": "test-id", "data": "' + escaped + '"}}'

@pytest.fixture
def set_pattern_config_req_obj(pc_obj) -> SetPatternConfigRequest:
    return SetPatternConfigRequest(pattern = Pattern("test-folder-1", "test-name-1", True), jsonData = pc_obj)

@pytest.fixture
def set_pattern_config_req_json(pc_json) -> str:
    escaped = pc_json.replace('"', '\\"')
    return '{"cmd": "toCtlrSet", "patternFileData": {"folders": "test-folder-1", "name": "test-name-1", "jsonData": "' + escaped + '"}}'

@pytest.fixture
def zc_obj() -> ZoneConfig:
    return ZoneConfig(26, [PortMapping("test-ctlr", 1, 2, 3, 4),PortMapping("test-ctlr", 5, 6, 7, 8)])

@pytest.fixture
def zc_json() -> str:
    return '{"numPixels":26,"portMap":[{"ctlrName":"test-ctlr","phyEndIdx":1,"phyPort":2,"phyStartIdx":3,"zoneRGBStartIdx":4}, {"ctlrName":"test-ctlr","phyEndIdx":5,"phyPort":6,"phyStartIdx":7,"zoneRGBStartIdx":8}]}'