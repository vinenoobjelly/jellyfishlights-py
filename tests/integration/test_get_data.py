from jellyfishlightspy.model import Pattern, ZoneConfig, PortMapping, State

def test_get_patterns(controller):
    patterns = controller.patterns
    assert patterns and len(patterns) > 0
    for pattern in patterns:
        assert type(pattern) is Pattern

def test_get_zones(controller):
    zones = controller.zones
    assert zones and len(zones) > 0
    assert len(controller.zone_names) == len(zones)
    for conf in zones.values():
        assert isinstance(conf, ZoneConfig)
        for pm in conf.portMap:
            assert isinstance(pm, PortMapping)

def test_get_zone_states(controller, helpers):
    zones = controller.zone_names
    test_zone = zones[0]
    state = controller.get_zone_state(test_zone)
    assert isinstance(state, State)
    states = controller.get_zone_states()
    assert set(zones) == set(states.keys())
    assert helpers.recursive_vars(state) == helpers.recursive_vars(states[test_zone])
    for zone, state in states.items():
        assert zone in zones
        assert isinstance(state, State)