import pytest
from time import sleep

def test_turn_on_off_single_zone(controller, zones):
    zone = zones[0]
    controller.turn_off([zone])
    assert controller.get_zone_state(zone).state == 0
    controller.turn_on([zone])
    assert controller.get_zone_state(zone).state == 1
    controller.turn_off([zone])
    assert controller.get_zone_state(zone).state == 0

def test_turn_on_off_all_zones(controller):
    controller.turn_off()
    assert all([state.state == 0 for state in controller.get_zone_states().values()])
    controller.turn_on()
    assert all([state.state == 1 for state in controller.get_zone_states().values()])
    controller.turn_off()
    assert all([state.state == 0 for state in controller.get_zone_states().values()])

# TODO: Figure out why the zone state is inconsistent - sometimes -1, sometimes 3
def test_apply_light_string(controller, zones):
    zone = zones[0]
    controller.apply_light_string([(255,255,255),(255,0,0),(0,255,0),(0,0,255)], 55, [zone])
    state = controller.get_zone_state(zone)
    assert state.state in [-1, 3]
    assert state.data.colors == [0,0,0,255,255,255,255,0,0,0,255,0,0,0,255]
    assert state.data.runData.brightness == 55
    controller.apply_light_string([(50,50,50)], 66)
    for zone, state in controller.get_zone_states().items():
        assert state.state in [-1, 3]
        assert state.data.colors == [0,0,0,50,50,50]
        assert state.data.runData.brightness == 66
    controller.turn_off()

def test_apply_color(controller, zones):
    zone = zones[0]
    controller.apply_color((255,0,0), 88, [zone])
    state = controller.get_zone_state(zone)
    assert state.state == 1
    assert state.data.colors == [255,0,0]
    assert state.data.runData.brightness == 88
    controller.apply_color((0,255,0), 77)
    for zone, state in controller.get_zone_states().items():
        assert state.state == 1
        assert state.data.colors == [0,255,0]
        assert state.data.runData.brightness == 77
    controller.turn_off()

def test_apply_pattern(controller, zones):
    controller.turn_off()
    p1 = "Colors/Orange"
    p2 = "Special Effects/Rainbow Waves"
    controller.apply_pattern(p1)
    for zone, state in controller.get_zone_states().items():
        assert state.state == 1
        assert state.file == p1
    zone = zones[0]
    controller.apply_pattern(p2, [zone])
    for name, state in controller.get_zone_states().items():
        assert state.state == 1
        assert state.file == p2 if name == zone else p1
    controller.turn_off()