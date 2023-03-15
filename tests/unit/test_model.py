import json
from jellyfishlightspy.model import RunData, RunPatternData, StateData, PatternName, PortMap, ZoneConfiguration
from jellyfishlightspy.helpers import to_json, from_json

def test_run_data(helpers, rd_obj, rd_json):
    o = helpers.assert_marshalling_works(rd_obj, rd_json)
    assert isinstance(o, RunData)

def test_run_pattern_data(helpers, rpd_obj, rpd_json):
    o = helpers.assert_marshalling_works(rpd_obj, rpd_json)
    assert isinstance(o, RunPatternData)
    assert isinstance(o.runData, RunData)

def test_state_data(helpers, sd_obj, sd_json):
    o = helpers.assert_marshalling_works(sd_obj, sd_json)
    assert isinstance(o, StateData)
    assert isinstance(o.data, RunPatternData)
    assert isinstance(o.data.runData, RunData)

def test_state_data_is_on(sd_obj):
    for i in range(-1, 4):
        sd_obj.state = i
        assert sd_obj.is_on == False if i == 0 else True

def test_state_data_special_serialization(sd_obj):
    assert isinstance(sd_obj.data, RunPatternData)
    sd_json = to_json(sd_obj)
    new_obj = json.loads(sd_json)
    assert isinstance(new_obj["data"], str)
    assert isinstance(from_json(sd_json).data, RunPatternData)

def test_pattern_name(helpers, pattern_list, pattern_json):
    o = helpers.assert_marshalling_works(pattern_list, pattern_json)
    assert isinstance(o, list)
    for p in o:
        assert isinstance(p, PatternName)

def test_zone_configuration(helpers, zc_obj, zc_json):
    o = helpers.assert_marshalling_works(zc_obj, zc_json)
    assert isinstance(o, ZoneConfiguration)
    assert o.portMap
    for p in o.portMap:
        assert isinstance(p, PortMap)

def test_pattern_name_str():
    f = "test-folder"
    n = "test-name"
    p = PatternName(f, n, True)
    assert str(p) == f"{f}/{n}"