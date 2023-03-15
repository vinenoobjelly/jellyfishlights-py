import json
from jellyfishlightspy.helpers import from_json, to_json

class Helpers:

    @staticmethod
    def recursive_vars(obj):
        if type(obj) is list:
            return [Helpers.recursive_vars(value) for value in obj]
        if hasattr(obj, "__dict__"):
            obj = vars(obj)
        if type(obj) is dict:
            for key, value in obj.items():
                obj[key] = Helpers.recursive_vars(value)
        return obj

    @staticmethod
    def assert_marshalling_works(obj, obj_json):
        s = to_json(obj)
        s_dict = json.loads(s)
        assert s_dict == json.loads(obj_json)
        o = from_json(s)
        assert Helpers.recursive_vars(o) == Helpers.recursive_vars(obj)
        return from_json(s) # do it again because o was converted to vars