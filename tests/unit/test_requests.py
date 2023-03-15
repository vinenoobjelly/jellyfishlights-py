def test_get_data_request(helpers, gd_req_obj, gd_req_json):
    helpers.assert_marshalling_works(gd_req_obj, gd_req_json)

def test_run_pattern_request(helpers, rp_req_obj, rp_req_json):
    helpers.assert_marshalling_works(rp_req_obj, rp_req_json)