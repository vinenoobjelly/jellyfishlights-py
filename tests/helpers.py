import json
from jellyfishlightspy.helpers import from_json, to_json

class Helpers:

    @staticmethod
    def recursive_vars(obj):
        # Serialze object to JSON
        sobj = json.dumps(obj, default=vars)
        # Deserialize JSON into a plain dictionary
        return json.loads(sobj)

    @staticmethod
    def assert_marshalling_works(obj, obj_json):
        # Serialze object to JSON (including special handling)
        s = to_json(obj)
        # Deserialize JSON into a plain dictionary for comparison
        s_dict = json.loads(s)
        # Compare dict to the provided reference JSON
        print(f"encoded: {s_dict}")
        print(f"reference: {json.loads(obj_json)}")
        assert s_dict == json.loads(obj_json)
        # Deserialize the JSON back into objects (including special handling)
        new_obj = from_json(s)
        # Compare the original object to the one that was serialized and then deserialized
        print(f"decoded: {Helpers.recursive_vars(new_obj)}")
        print(f"reference: {Helpers.recursive_vars(obj)}")
        assert Helpers.recursive_vars(new_obj) == Helpers.recursive_vars(obj)
        return new_obj