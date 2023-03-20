import json
from jellyfishlightspy.model import RunConfig, PatternConfig, ZoneState, Pattern, PortMapping, ZoneConfig, ControllerVersion
from jellyfishlightspy.helpers import to_json, from_json

def test_controller_version(helpers, cv_obj, cv_json):
    o = helpers.assert_marshalling_works(cv_obj, cv_json)
    assert isinstance(o, ControllerVersion)

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