import pytest
from time import sleep

def test_turn_on_off_single_zone(controller):
    zone = controller.zone_names[0]
    controller.turn_off([zone])
    assert not controller.get_zone_state(zone).is_on
    controller.turn_on([zone])
    assert controller.get_zone_state(zone).is_on
    controller.turn_off([zone])
    assert not controller.get_zone_state(zone).is_on

def test_turn_on_off_all_zones(controller):
    controller.turn_off()
    assert all(not state.is_on for state in controller.get_zone_states().values())
    controller.turn_on()
    assert all(state.is_on for state in controller.get_zone_states().values())
    controller.turn_off()
    assert all(not state.is_on for state in controller.get_zone_states().values())

def test_apply_light_string(controller):
    zone = controller.zone_names[0]
    controller.apply_light_string([(255, 255, 255), (255, 0, 0), (0, 255, 0) ,(0, 0, 255)], 55, [zone])
    state = controller.get_zone_state(zone)
    assert state.is_on and state.state in [-1, 3]
    assert state.data.colors == [0, 0, 0, 255, 255, 255, 255, 0, 0, 0, 255, 0, 0, 0, 255]
    assert state.data.runData.brightness == 55
    controller.turn_off([zone])
    controller.apply_light_string([(50, 50, 50)], 66)
    for zone, state in controller.get_zone_states().items():
        assert state.is_on and state.state in [-1, 3]
        assert state.data.colors == [0, 0, 0, 50, 50, 50]
        assert state.data.runData.brightness == 66

def test_apply_color(controller):
    zone = controller.zone_names[0]
    controller.apply_color((255, 0, 0), 88, [zone])
    state = controller.get_zone_state(zone)
    assert state.is_on
    assert state.data.colors == [255, 0, 0]
    assert state.data.runData.brightness == 88
    controller.turn_off([zone])
    controller.apply_color((0, 255, 0), 77)
    for zone, state in controller.get_zone_states().items():
        assert state.is_on
        assert state.data.colors == [0, 255, 0]
        assert state.data.runData.brightness == 77

def test_apply_pattern(controller):
    p1 = "Colors/Orange"
    p2 = "Special Effects/Rainbow Waves"
    controller.apply_pattern(p1)
    for zone, state in controller.get_zone_states().items():
        assert state.is_on
        assert state.file == p1
    zone = controller.zone_names[0]
    controller.turn_off([zone])
    controller.apply_pattern(p2, [zone])
    for name, state in controller.get_zone_states().items():
        assert state.is_on
        assert state.file == p2 if name == zone else p1

def test_apply_pattern_config(controller):
    config = controller.get_pattern_config("Colors/Green")
    config.colors.extend([0, 0, 0])
    config.type = "Chase"
    config.direction = "Center"
    config.spaceBetweenPixels = 8
    config.effectBetweenPixels = "Progression"
    config.runData.speed = 1
    test_zone = controller.zone_names[0]
    controller.apply_pattern_config(config, [test_zone])
    state = controller.get_zone_state(test_zone)
    assert state.is_on
    assert state.data is not None
    assert state.data.colors == config.colors
    assert state.data.type == config.type
    assert state.data.direction == config.direction
    assert state.data.spaceBetweenPixels == config.spaceBetweenPixels
    assert state.data.effectBetweenPixels == config.effectBetweenPixels
    assert state.data.runData.speed == config.runData.speed
    assert state.data.colors == config.colors
    controller.apply_pattern_config(config)
    for state in controller.get_zone_states().values():
        assert state.is_on
        assert state.data is not None
        assert state.data.colors == config.colors
        assert state.data.type == config.type
        assert state.data.direction == config.direction
        assert state.data.spaceBetweenPixels == config.spaceBetweenPixels
        assert state.data.effectBetweenPixels == config.effectBetweenPixels
        assert state.data.runData.speed == config.runData.speed
        assert state.data.colors == config.colors
