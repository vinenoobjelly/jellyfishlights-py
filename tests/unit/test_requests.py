def test_get_data_request(helpers, get_req_obj, get_req_json):
    helpers.assert_marshalling_works(get_req_obj, get_req_json)

def test_run_pattern_request(helpers, set_req_obj, set_req_json):
    helpers.assert_marshalling_works(set_req_obj, set_req_json)