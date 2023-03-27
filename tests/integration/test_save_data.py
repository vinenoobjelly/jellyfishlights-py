import pytest
import time
from jellyfishlightspy.model import Pattern, ScheduleEvent, ScheduleEventAction, ZoneConfig, PortMapping
from jellyfishlightspy.helpers import JellyFishException

def test_set_name(controller):
    test_name = "**INT TEST** ctlrName"
    orig_name = controller.name
    assert test_name != orig_name
    controller.set_name(test_name)
    assert controller.name == test_name
    controller.set_name(orig_name)
    assert controller.name == orig_name

def test_save_and_delete_pattern(controller):
    config = controller.get_pattern_config("Colors/Blue")
    config.colors.extend([0, 0, 0])
    config.type = "Chase"
    config.direction = "Center"
    config.spaceBetweenPixels = 8
    config.effectBetweenPixels = "Progression"
    config.runData.speed = 1
    pattern = Pattern("INT_TESTS", "Blue Waves")
    name = str(pattern)
    controller.save_pattern(name, config)
    assert name in controller.pattern_names
    assert name in controller.pattern_configs
    assert next((p for p in controller.pattern_list if p.folders == pattern.folders and p.name == pattern.name), False)
    controller.apply_pattern(name)
    for state in controller.get_zone_states().values():
        assert state.file == name
    controller.delete_pattern(name)
    assert name not in controller.pattern_names
    assert name not in controller.pattern_configs
    assert not next((p for p in controller.pattern_list if p.folders == pattern.folders and p.name == pattern.name), False)
    with pytest.raises(JellyFishException):
        controller.delete_pattern(name)
    # This fails every other test run... not sure why
    # Seems the controller will sometimes delete the parent folder if it's empty?
    # controller.delete_pattern("INT_TESTS/")
    # assert not next((p for p in controller.pattern_list if p.folders == pattern.folders), False)
    # with pytest.raises(JellyFishException):
    #     controller.delete_pattern("INT_TESTS/")


def test_save_and_delete_zones(controller):
    orig_zones = controller.zone_configs
    hostname = controller.hostname
    test_zones = {
        "test-zone-1": ZoneConfig([PortMapping(1, 0, 10),PortMapping(1, 11, 20)]),
        "test-zone-2": ZoneConfig([PortMapping(1, 21, 50)]),
        "test-zone-3": ZoneConfig([PortMapping(1, 100, 51, 51),PortMapping(2, 0, 100)])
    }
    controller.set_zone_configs(test_zones)
    assert set(test_zones.keys()) == set(controller.zone_names)
    for zone, config in test_zones.items():
        assert config.numPixels == controller.zone_configs[zone].numPixels
        assert len(config.portMap) == len(controller.zone_configs[zone].portMap)
        for pm in config.portMap:
            assert pm.ctlrName == hostname
    del_zone = "test-zone-1"
    controller.delete_zone(del_zone)
    assert set(["test-zone-2", "test-zone-3"]) == set(controller.zone_names)
    with pytest.raises(JellyFishException):
        controller.delete_zone(del_zone)
    controller.add_zone(del_zone, test_zones[del_zone])
    assert set(test_zones.keys()) == set(controller.zone_names)
    with pytest.raises(JellyFishException):
        controller.add_zone(del_zone, test_zones[del_zone])
    controller.set_zone_configs(orig_zones)


def test_get_and_set_calendar_schedule(controller):
    orig_events = controller.get_calendar_schedule()
    test_pattern = controller.pattern_names[0]
    test_zones = controller.zone_names
    e1 = ScheduleEvent(
        label = "INT_TEST_1",
        days = ["20231231", "20230101", "20230102"],
        actions = [
            ScheduleEventAction("RUN", "sunset", 0, 50, test_pattern, test_zones),
            ScheduleEventAction("STOP", "sunrise", 0, -25, "", test_zones)
        ]
    )
    e2 = ScheduleEvent(
        label = "INT_TEST_2",
        days = ["20230704"],
        actions = [
            ScheduleEventAction("RUN", "time", 20, 00, test_pattern, test_zones),
            ScheduleEventAction("STOP", "time", 5, 00, "", test_zones)
        ]
    )
    controller.add_calendar_event(e1)
    assert next((e for e in controller.calendar_schedule if e.label == e1.label), False)
    events = controller.calendar_schedule
    events.append(e2)
    controller.set_calendar_schedule(events)
    assert next((e for e in controller.calendar_schedule if e.label == e1.label), False)
    assert next((e for e in controller.calendar_schedule if e.label == e2.label), False)
    controller.set_calendar_schedule(orig_events)
    assert len(controller.calendar_schedule) == len(orig_events)
    assert not next((e for e in controller.calendar_schedule if e.label == e1.label), False)
    assert not next((e for e in controller.calendar_schedule if e.label == e2.label), False)


def test_get_and_set_daily_schedule(controller):
    orig_events = controller.get_daily_schedule()
    test_pattern = controller.pattern_names[0]
    test_zones = controller.zone_names
    e1 = ScheduleEvent(
        label = "INT_TEST_1",
        days = ["M", "W", "F"],
        actions = [
            ScheduleEventAction("RUN", "sunset", 0, 50, test_pattern, test_zones),
            ScheduleEventAction("STOP", "sunrise", 0, -25, "", test_zones)
        ]
    )
    e2 = ScheduleEvent(
        label = "INT_TEST_2",
        days = ["T", "TH"],
        actions = [
            ScheduleEventAction("RUN", "time", 20, 00, test_pattern, test_zones),
            ScheduleEventAction("STOP", "time", 5, 00, "", test_zones)
        ]
    )
    controller.add_daily_event(e1)
    assert next((e for e in controller.daily_schedule if e.label == e1.label), False)
    events = controller.daily_schedule
    events.append(e2)
    controller.set_daily_schedule(events)
    assert next((e for e in controller.daily_schedule if e.label == e1.label), False)
    assert next((e for e in controller.daily_schedule if e.label == e2.label), False)
    controller.set_daily_schedule(orig_events)
    assert len(controller.daily_schedule) == len(orig_events)
    assert not next((e for e in controller.daily_schedule if e.label == e1.label), False)
    assert not next((e for e in controller.daily_schedule if e.label == e2.label), False)