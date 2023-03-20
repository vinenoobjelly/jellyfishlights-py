from jellyfishlightspy.model import Pattern, ZoneConfig, PortMapping, State, PatternConfig
from jellyfishlightspy.helpers import validate_pattern_config

def test_get_patterns(controller):
    patterns = controller.pattern_list
    assert patterns and len(patterns) > 0
    for pattern in patterns:
        assert type(pattern) is Pattern

def test_get_zones(controller):
    zones = controller.zone_configs
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

def test_get_pattern_configs(controller, helpers):
    patterns = controller.pattern_names
    test_pattern = patterns[0]
    config = controller.get_pattern_config(test_pattern)
    assert isinstance(config, PatternConfig)
    configs = controller.get_pattern_configs()
    assert set(patterns) == set(configs.keys())
    assert helpers.recursive_vars(config) == helpers.recursive_vars(configs[test_pattern])
    for pattern, config in configs.items():
        assert pattern in patterns
        assert isinstance(config, PatternConfig)

def test_validate_pattern_configs(controller):
    configs = controller.pattern_configs.values()
    zones = controller.zone_names
    for config in configs:
        validate_pattern_config(config, zones)