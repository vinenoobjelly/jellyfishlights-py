from jellyfishlightspy.model import ZoneState, PatternConfig

def test_get_data_request(helpers, get_req_obj, get_req_json):
    helpers.assert_marshalling_works(get_req_obj, get_req_json)

def test_set_state_request(helpers, set_state_req_obj, set_state_req_json):
    o = helpers.assert_marshalling_works(set_state_req_obj, set_state_req_json)
    assert type(o["runPattern"]) is ZoneState

def test_set_pattern_config_request(helpers, set_pattern_config_req_obj, set_pattern_config_req_json):
    o = helpers.assert_marshalling_works(set_pattern_config_req_obj, set_pattern_config_req_json)
    assert type(o["patternFileData"]["jsonData"]) is PatternConfig