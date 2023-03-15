import pytest
import time
from threading import Thread
from jellyfishlightspy.model import PatternName
from jellyfishlightspy.helpers import (
    JellyFishLightsException,
    TimelyEvent,
    validate_brightness,
    validate_intensity,
    validate_rgb,
    validate_pattern,
    validate_zones,
)

# Note: tests in model.py sufficiently cover from_json, to_json, _stringify_state_data, and _object_hook

def test_validate_brightness():
    validate_brightness(100)
    validate_brightness(0)
    validate_brightness(50)
    with pytest.raises(JellyFishLightsException):
        validate_brightness(-1)
    with pytest.raises(JellyFishLightsException):
        validate_brightness(101)
    with pytest.raises(JellyFishLightsException):
        validate_brightness(None)
    with pytest.raises(JellyFishLightsException):
        validate_brightness("256")

def test_validate_intensity():
    validate_intensity(0)
    validate_intensity(255)
    validate_intensity(100)
    with pytest.raises(JellyFishLightsException):
        validate_intensity(-1)
    with pytest.raises(JellyFishLightsException):
        validate_intensity(256)
    with pytest.raises(JellyFishLightsException):
        validate_intensity(None)
    with pytest.raises(JellyFishLightsException):
        validate_intensity("256")

def test_validate_rgb():
    validate_rgb((0,0,0))
    validate_rgb((255,255,255))
    validate_rgb((100,100,100))
    with pytest.raises(JellyFishLightsException):
        validate_rgb((-1,100,100))
    with pytest.raises(JellyFishLightsException):
        validate_rgb((0,100,256))
    with pytest.raises(JellyFishLightsException):
        validate_rgb((0,1000,0))
    with pytest.raises(JellyFishLightsException):
        validate_rgb((0,0,0,0))
    with pytest.raises(JellyFishLightsException):
        validate_rgb((0,0))
    with pytest.raises(JellyFishLightsException):
        validate_rgb([255,255,255])
    with pytest.raises(JellyFishLightsException):
        validate_rgb(None)
    with pytest.raises(JellyFishLightsException):
        validate_rgb(100)

def test_validate_patterns():
    valid_patterns = [PatternName("one", "plus two", False), PatternName("three and", "four", False)]
    validate_pattern("one/plus two", valid_patterns)
    validate_pattern("three and/four", valid_patterns)
    with pytest.raises(JellyFishLightsException):
        validate_pattern("bad/pattern", valid_patterns)

def test_validate_zones(zc_obj):
    valid_zones = {
        "zone1": zc_obj,
        "zone2": zc_obj
    }
    validate_zones(list(valid_zones), valid_zones)
    validate_zones([list(valid_zones)[0]], valid_zones)
    with pytest.raises(JellyFishLightsException):
        validate_zones(["bad-zone"], valid_zones)

def test_timely_event():
    event = TimelyEvent()
    assert not event.is_set()
    event.set()
    assert event.is_set()
    event.clear()
    assert not event.is_set()
    thread = Thread(target = lambda: event.wait(), daemon = True)
    thread.start()
    time.sleep(.1)
    assert thread.is_alive()
    event.set()
    thread.join(timeout = .1)
    assert not thread.is_alive()
    start = time.perf_counter()
    event.set()
    thread = Thread(target = lambda: event.wait(after_ts = start), daemon = True)
    thread.start()
    thread.join(timeout = .1)
    assert not thread.is_alive()
