import pytest
import json
from typing import List
from jellyfishlightspy.helpers import to_json, from_json
from jellyfishlightspy.model import (
    RunConfig,
    PatternConfig,
    ZoneState,
    Pattern,
    ZoneConfig,
    PortMapping,
    FirmwareVersion,
    ScheduleEvent,
    ScheduleEventAction,
)
from jellyfishlightspy.requests import GetRequest, SetZoneStateRequest, SetPatternConfigRequest
from tests.helpers import Helpers

@pytest.fixture
def helpers() -> Helpers:
    return Helpers

@pytest.fixture
def cv_obj() -> FirmwareVersion:
    return FirmwareVersion("test-ver", "test-details", True)

@pytest.fixture
def cv_json() -> str:
    return '{"ver": "test-ver", "details": "test-details", "isUpdate": true}'

@pytest.fixture
def rc_obj() -> RunConfig:
    return RunConfig(speed=20, brightness=100, effect="test-effect", effectValue=1, rgbAdj=[2,3,4])

@pytest.fixture
def rc_json() -> str:
    return '{"speed": 20, "brightness": 100, "effect": "test-effect", "effectValue": 1, "rgbAdj": [2, 3, 4]}'

@pytest.fixture
def pc_obj(rc_obj) -> PatternConfig:
    return PatternConfig(type="test-type", colors=[0,1,2,3,4,5], runData=rc_obj, direction="test-direction", spaceBetweenPixels=5, numOfLeds=6, skip=7, effectBetweenPixels="test-effect-between-pixels", colorPos=[8, 9, 10], cursor=11, ledOnPos={"0": [], "1": [1]}, soffitZone="test-zone-1")

@pytest.fixture
def pc_json(rc_json) -> str:
    return '{"type": "test-type", "colors": [0, 1, 2, 3, 4, 5], "runData": ' + rc_json + ', "direction": "test-direction", "spaceBetweenPixels": 5, "numOfLeds": 6, "skip": 7, "effectBetweenPixels": "test-effect-between-pixels", "colorPos": [8, 9, 10], "cursor": 11, "ledOnPos": {"0": [], "1": [1]}, "soffitZone": "test-zone-1"}'

@pytest.fixture
def s_obj(pc_obj) -> ZoneState:
    return ZoneState(state=1, zoneName=["test-zone-1", "test-zone-2"], file="test-file", id="test-id", data=pc_obj)

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
def set_state_req_obj(pc_obj) -> SetZoneStateRequest:
    return SetZoneStateRequest(1, ["test-zone-1", "test-zone-2"], file="test-folder/test-name", id="test-id", data=pc_obj)

@pytest.fixture
def set_state_req_json(pc_json) -> str:
    escaped = pc_json.replace('"', '\\"')
    return '{"cmd": "toCtlrSet", "runPattern": {"state": 1, "zoneName": ["test-zone-1", "test-zone-2"], "file": "test-folder/test-name", "id": "test-id", "data": "' + escaped + '"}}'

@pytest.fixture
def set_pattern_config_req_obj(pc_obj) -> SetPatternConfigRequest:
    return SetPatternConfigRequest(pattern=Pattern("test-folder-1", "test-name-1", True), jsonData=pc_obj)

@pytest.fixture
def set_pattern_config_req_json(pc_json) -> str:
    escaped = pc_json.replace('"', '\\"')
    return '{"cmd": "toCtlrSet", "patternFileData": {"folders": "test-folder-1", "name": "test-name-1", "jsonData": "' + escaped + '"}}'

@pytest.fixture
def zc_obj() -> ZoneConfig:
    return ZoneConfig([PortMapping(1, 0, 10, 0, "test-ctlr"),PortMapping(1, 11, 20, 20, "test-ctlr")], 21)

@pytest.fixture
def zc_json() -> str:
    return '{"numPixels":21,"portMap":[{"ctlrName":"test-ctlr","phyPort":1,"phyStartIdx":0,"phyEndIdx":10,"zoneRGBStartIdx":0}, {"ctlrName":"test-ctlr","phyPort":1,"phyStartIdx":11,"phyEndIdx":20,"zoneRGBStartIdx":20}]}'

@pytest.fixture
def se_obj() -> ScheduleEvent:
    return ScheduleEvent(
        label = "",
        days = ["M", "T", "W"],
        actions = [
            ScheduleEventAction("RUN", "sunset", 0, 50, "test-pattern", ["test-zone-1", "test-zone-2"]),
            ScheduleEventAction("STOP", "sunrise", 0, -25, "", ["test-zone-1", "test-zone-2"])
        ]
    )

@pytest.fixture
def se_json() -> str:
    return '{"label": "", "days": ["M", "T", "W"], "actions": [{"type": "RUN", "startFrom": "sunset", "hour": 0, "minute": 50, "patternFile": "test-pattern", "zones": ["test-zone-1", "test-zone-2"]}, {"type": "STOP", "startFrom": "sunrise", "hour": 0, "minute": -25, "patternFile": "", "zones": ["test-zone-1", "test-zone-2"]}]}'