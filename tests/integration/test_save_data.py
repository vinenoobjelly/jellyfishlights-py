import pytest
from jellyfishlightspy.model import Pattern

def test_save_pattern(controller):
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
    controller.delete_pattern("INT_TESTS/")
    assert not next((p for p in controller.pattern_list if p.folders == pattern.folders), False)