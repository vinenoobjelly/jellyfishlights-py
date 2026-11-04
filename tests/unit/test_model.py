import json
from jellyfishlightspy.model import (
    RunConfig,
    PatternConfig,
    ZoneState,
    Pattern,
    PortMapping,
    ZoneConfig,
    FirmwareVersion,
    ScheduleEvent,
    ScheduleEventAction,
)
from jellyfishlightspy.helpers import to_json, from_json

def test_firmware_version(helpers, cv_obj, cv_json):
    o = helpers.assert_marshalling_works(cv_obj, cv_json)
    assert isinstance(o, FirmwareVersion)

def test_run_config(helpers, rc_obj, rc_json):
    o = helpers.assert_marshalling_works(rc_obj, rc_json)
    assert isinstance(o, RunConfig)

def test_pattern_config(helpers, pc_obj, pc_json):
    o = helpers.assert_marshalling_works(pc_obj, pc_json)
    assert isinstance(o, PatternConfig)
    assert isinstance(o.runData, RunConfig)

def test_state(helpers, s_obj, s_json):
    o = helpers.assert_marshalling_works(s_obj, s_json)
    assert isinstance(o, ZoneState)
    assert isinstance(o.data, PatternConfig)
    assert isinstance(o.data.runData, RunConfig)

def test_state_is_on():
    sd = ZoneState(1, [])
    for i in range(-1, 4):
        sd.state = i
        assert sd.is_on == False if i == 0 else True

def test_state_special_serialization(s_obj):
    assert isinstance(s_obj.data, PatternConfig)
    s_json = to_json(s_obj)
    new_obj = json.loads(s_json)
    assert isinstance(new_obj["data"], str)
    assert isinstance(from_json(s_json).data, PatternConfig)

def test_pattern(helpers, pattern_list, pattern_json):
    o = helpers.assert_marshalling_works(pattern_list, pattern_json)
    assert isinstance(o, list)
    for p in o:
        assert isinstance(p, Pattern)

def test_zone_config(helpers, zc_obj, zc_json):
    o = helpers.assert_marshalling_works(zc_obj, zc_json)
    assert isinstance(o, ZoneConfig)
    assert o.portMap
    for p in o.portMap:
        assert isinstance(p, PortMapping)

def test_pattern_str():
    f = "test-folder"
    n = "test-name"
    p = Pattern(f, n, True)
    assert str(p) == f"{f}/{n}"
    p2 = Pattern.from_str(str(p))
    assert p.folders == p2.folders
    assert p.name == p2.name

def test_schedule_event(helpers, se_obj, se_json):
    o = helpers.assert_marshalling_works(se_obj, se_json)
    assert isinstance(o, ScheduleEvent)
    for action in o.actions:
        assert isinstance(action, ScheduleEventAction)
def test_music_pattern_config():
    # Music Box patterns have a nested musicSettings object that also has "colors" (#44 in hass-jellyfish-lighting)
    music_settings = {"musicType": "Bar Overlay", "frequencies": ["Bass"], "frequencyMultipliers": [1.0], "colors": [{"R": 255, "G": 40, "B": 0}, {"R": 0, "G": 0, "B": 0}], "beatThreshold": 50.0, "direction": "center", "tipSize": 2}
    data = {"type": "Music", "colors": [80, 0, 120, 255, 60, 0], "spaceBetweenPixels": 1, "effectBetweenPixels": "No Color Transform", "skip": 1, "numOfLeds": 1, "runData": {"speed": 1, "brightness": 100, "effect": "No Effect", "effectValue": 0, "rgbAdj": [100, 100, 100]}, "direction": "Left", "musicSettings": music_settings}
    msg = json.dumps({"activatedBy": "network_command", "data": json.dumps(data), "file": "_JF-MUSIC/Test", "id": "Zone1", "state": 1, "zoneName": ["Zone1"]})
    o = from_json(msg)
    assert isinstance(o, ZoneState)
    assert isinstance(o.data, PatternConfig)
    assert o.data.type == "Music"
    assert isinstance(o.data.runData, RunConfig)
    assert o.data.musicSettings == music_settings
    # musicSettings is preserved when the config is sent back to the controller
    assert from_json(to_json(o)).data.musicSettings == music_settings

def test_colors_without_type_is_not_pattern_config():
    assert from_json('{"colors": [{"R": 1, "G": 2, "B": 3}]}') == {"colors": [{"R": 1, "G": 2, "B": 3}]}
