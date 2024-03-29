import pytest
from jellyfishlightspy.model import Pattern, PatternConfig, RunConfig, ZoneConfig, PortMapping
from jellyfishlightspy.helpers import JellyFishException
from jellyfishlightspy.validators import (
    validate_brightness,
    validate_rgb,
    validate_patterns,
    validate_zones,
    validate_pattern_config,
    validate_schedule_event,
    validate_schedule_event_action,
    validate_port_mapping,
    validate_zone_config,
)

def test_validate_brightness():
    validate_brightness(100)
    validate_brightness(0)
    validate_brightness(50)
    with pytest.raises(JellyFishException):
        validate_brightness(-1)
    with pytest.raises(JellyFishException):
        validate_brightness(101)
    with pytest.raises(JellyFishException):
        validate_brightness(None)
    with pytest.raises(JellyFishException):
        validate_brightness("256")


def test_validate_rgb():
    validate_rgb((0,0,0))
    validate_rgb((255,255,255))
    validate_rgb((100,100,100))
    with pytest.raises(JellyFishException):
        validate_rgb((-1,100,100))
    with pytest.raises(JellyFishException):
        validate_rgb((0,100,256))
    with pytest.raises(JellyFishException):
        validate_rgb((0,1000,0))
    with pytest.raises(JellyFishException):
        validate_rgb((0,0,0,0))
    with pytest.raises(JellyFishException):
        validate_rgb((0,0))
    with pytest.raises(JellyFishException):
        validate_rgb([255,255,255])
    with pytest.raises(JellyFishException):
        validate_rgb(None)
    with pytest.raises(JellyFishException):
        validate_rgb((None, 100, 100))
    with pytest.raises(JellyFishException):
        validate_rgb((100, '100', 100))
    with pytest.raises(JellyFishException):
        validate_rgb(100)


def test_validate_zone_config():
    config = ZoneConfig([PortMapping(1, 0, 10, 0, "test-ctlr"),PortMapping(1, 11, 20, 20, "test-ctlr")], 21)
    validate_zone_config(config)

    orig_map = config.portMap
    config.portMap = tuple(orig_map)
    with pytest.raises(JellyFishException):
        validate_zone_config(config)
    config.portMap = [1, 2]
    with pytest.raises(JellyFishException):
        validate_zone_config(config)
    config.portMap = orig_map
    validate_zone_config(config)

    config.numPixels = 20
    with pytest.raises(JellyFishException):
        validate_zone_config(config)
    config.numPixels = 21
    validate_zone_config(config)


def test_validate_port_mapping():
    pm = PortMapping(1, 0, 10, 0, "test-ctlr")
    validate_port_mapping(pm)

    pm.phyPort = 0
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.phyPort = "1"
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.phyPort = None
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.phyPort = 1
    validate_port_mapping(pm)

    pm.phyStartIdx = -1
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.phyStartIdx = "0"
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.phyStartIdx = None
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.phyStartIdx = 0
    validate_port_mapping(pm)

    pm.phyEndIdx = -1
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.phyEndIdx = "0"
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.phyEndIdx = None
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.phyEndIdx = 10
    validate_port_mapping(pm)

    pm.ctlrName = None
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.ctlrName = 1
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.ctlrName = "test-ctlr"
    validate_port_mapping(pm)

    pm.zoneRGBStartIdx = 2
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.zoneRGBStartIdx = "10"
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.zoneRGBStartIdx = None
    with pytest.raises(JellyFishException):
        validate_port_mapping(pm)
    pm.zoneRGBStartIdx = 0
    validate_port_mapping(pm)
    pm.zoneRGBStartIdx = 10
    validate_port_mapping(pm)


def test_validate_patterns():
    valid_patterns = ["one/plus two", "three and/four"]
    validate_patterns([valid_patterns[0]], valid_patterns)
    validate_patterns(valid_patterns, valid_patterns)
    with pytest.raises(JellyFishException):
        validate_patterns(["bad/pattern"], valid_patterns)


def test_validate_pattern_config():
    config = PatternConfig(
        colors = [255, 255, 255],
        type = "Color",
        runData = RunConfig(
            brightness = 100,
            speed = 10,
            effect = "No Effect",
            effectValue = 0,
            rgbAdj = [100, 100, 100]
        ),
        colorPos = [],
        direction = "Center",
        spaceBetweenPixels = 2,
        numOfLeds = 2,
        skip = 2,
        effectBetweenPixels = "Progression",
        cursor = -1,
        ledOnPos = {},
        soffitZone = "test-zone-1"
    )
    assert validate_pattern_config(config, [config.soffitZone])

    config.colors.append(255)
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.colors.append(255)
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.colors.append(-1)
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.colors.pop()
    config.colors.append(0)
    assert validate_pattern_config(config, [config.soffitZone])

    config.type = "bad type"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.type = "Chase"
    assert validate_pattern_config(config, [config.soffitZone])

    config.runData.brightness = 101
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.runData.brightness = 0
    assert validate_pattern_config(config, [config.soffitZone])

    config.runData.speed = "10"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.runData.speed = 1
    assert validate_pattern_config(config, [config.soffitZone])

    config.runData.effect = "Twinkles"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.runData.effect = "Twinkle"
    assert validate_pattern_config(config, [config.soffitZone])

    config.runData.effectValue = "10"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.runData.effectValue = 1
    assert validate_pattern_config(config, [config.soffitZone])

    config.runData.rgbAdj.append(255)
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.runData.rgbAdj = [-1, 100, 100]
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.runData.rgbAdj = [0, 100, 256]
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.runData.rgbAdj = "[0, 100, 256]"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.runData.rgbAdj = [255, 255, 255]
    assert validate_pattern_config(config, [config.soffitZone])

    config.colorPos = "10"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.colorPos = [1, 2, 3, 4]
    assert validate_pattern_config(config, [config.soffitZone])

    config.direction = "Up"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.direction = "Right"
    assert validate_pattern_config(config, [config.soffitZone])

    config.spaceBetweenPixels = "10"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.spaceBetweenPixels = 5
    assert validate_pattern_config(config, [config.soffitZone])

    config.numOfLeds = "10"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.numOfLeds = 5
    assert validate_pattern_config(config, [config.soffitZone])

    config.skip = "10"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.skip = 5
    assert validate_pattern_config(config, [config.soffitZone])

    config.cursor = "10"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, [config.soffitZone])
    config.cursor = 5
    assert validate_pattern_config(config, [config.soffitZone])

    config.soffitZone = "bad zone"
    with pytest.raises(JellyFishException):
        assert validate_pattern_config(config, ["test-zone-1"])


def test_validate_zones(zc_obj):
    valid_zones = ["zone1", "zone2"]
    validate_zones(valid_zones, valid_zones)
    validate_zones([valid_zones[0]], valid_zones)
    with pytest.raises(JellyFishException):
        validate_zones(["bad/zone"], valid_zones)


def test_validate_schedule_event(se_obj):
    valid_patterns = [se_obj.actions[0].patternFile]
    valid_zones = se_obj.actions[0].zones
    validate_schedule_event(se_obj, False, valid_patterns, valid_zones)
    se_obj.label = 1
    with pytest.raises(JellyFishException):
        validate_schedule_event(se_obj, False, valid_patterns, valid_zones)
    se_obj.label = ""

    orig_days = se_obj.days.copy()
    se_obj.days = ["MON", "TUE"]
    with pytest.raises(JellyFishException):
        validate_schedule_event(se_obj, False, valid_patterns, valid_zones)
    se_obj.days = ["20221231", "20230101"]
    validate_schedule_event(se_obj, True, valid_patterns, valid_zones)
    se_obj.days = ["221231", "220101"]
    with pytest.raises(JellyFishException):
        validate_schedule_event(se_obj, True, valid_patterns, valid_zones)
    se_obj.days = ["1231", "0101"]
    with pytest.raises(JellyFishException):
        validate_schedule_event(se_obj, True, valid_patterns, valid_zones)
    se_obj.days = ["20221231", "20230101"]
    validate_schedule_event(se_obj, True, valid_patterns, valid_zones)
    se_obj.days = orig_days
    validate_schedule_event(se_obj, False, valid_patterns, valid_zones)

    se_obj.actions[0].zones.extend("another-zone")
    with pytest.raises(JellyFishException):
        validate_schedule_event(se_obj, False, valid_patterns, valid_zones)
    se_obj.actions[0].zones.pop()


def test_validate_schedule_event_action(se_obj):
    action = se_obj.actions[0]
    valid_patterns = [action.patternFile]
    valid_zones = action.zones
    validate_schedule_event_action(action, valid_patterns, valid_zones)

    orig_type = action.type
    action.type = "blackjack"
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.type = orig_type

    orig_start = action.startFrom
    action.startFrom = "square-one"
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.startFrom = orig_start

    orig_hour = action.hour
    action.hour = "12"
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.hour = 24
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.hour = -1
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.hour = 0
    validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.hour = 23
    validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.hour = orig_hour

    orig_min = action.minute
    action.startFrom = "time"
    action.minute = "23"
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.minute = -1
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.minute = 60
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.minute = 59
    validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.minute = 0
    validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.startFrom = "sunset"
    action.minute = "5"
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.minute = -60
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.minute = 60
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.minute = 9
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.minute = 55
    validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.minute = 0
    validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.minute = -55
    validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.minute = orig_min

    action.type = "RUN"
    action.patternFile = ["pattern"]
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.patternFile = valid_patterns[0]
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, ["bad-pattern"], valid_zones)
    action.type = orig_type

    action.zones = valid_zones[0]
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, valid_zones)
    action.zones = valid_zones
    with pytest.raises(JellyFishException):
        validate_schedule_event_action(action, valid_patterns, ["bad-zone"])