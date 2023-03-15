from jellyfishlightspy.model import PatternName, ZoneConfiguration, PortMap, StateData

def test_get_patterns(controller):
    patterns = controller.get_patterns()
    assert patterns and len(patterns) > 0
    assert controller.patterns and len(controller.patterns) == len(patterns)
    for pattern in patterns:
        assert type(pattern) is PatternName

def test_get_zones(controller):
    zones = controller.get_zones()
    assert zones and len(zones) > 0
    assert controller.zones and len(controller.zones) == len(zones)
    for conf in zones.values():
        assert isinstance(conf, ZoneConfiguration)
        for pm in conf.portMap:
            assert isinstance(pm, PortMap)

def test_get_zone_states(controller, helpers):
    zones = list(controller.get_zones().keys())
    test_zone = zones[0]
    state = controller.get_zone_state(test_zone)
    assert isinstance(state, StateData)
    states = controller.get_zone_states()
    assert len(zones) == len(states)
    assert set(zones) == set(states.keys())
    assert helpers.recursive_vars(state) == helpers.recursive_vars(states[test_zone])
    for zone, state in states.items():
        assert zone in zones
        assert isinstance(state, StateData)