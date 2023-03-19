# Python wrapper for JellyFish Lights web socket API

~~The hope is to make this a pip installable package~~
Now available through pypi/pip!

To install:

- pip install jellyfishlights-py

## Current capabalilities

- Connect to a local JellyFish Lighting controller over websocket
- Retrieve the following data:
  - Zone configuration
  - Preset patterns and their configurations
  - Zone states
- Turn zones on and off
- Activate a preset pattern
- Set lights to a solid color with brightness control
- Set any individual lights you want with brightness control
- Activate a custom pattern configuration

## Example

```python
from jellyfishlightspy import JellyFishController
import logging

# Debug logging exposes the messages sent to and received from the controller
logging.basicConfig(level = logging.DEBUG)

# Create a controller object and connect
jfc = JellyFishController('192.168.0.245') # hostname also works
jfc.connect()

# Print the currently configured zones
print(f"Zones: {jfc.zone_names}")

# Print the currently configured patterns
print(f"Patterns: {jfc.pattern_names}")

# Run a preset pattern on all zones
# Note: Many commands have an optional zones parameter.
# If not filled, it defaults to all zones
jfc.apply_pattern('Special Effects/Red Waves')

# Set 'front-zone' and 'back-zone' to a solid color (white @ 100% brightness in this case)
jfc.apply_color((255, 255, 255), 100, ['front-zone', 'back-zone'])

# Set individual lights on the 'porch-zone' zone at 100% brightness
lights = [
    (255, 0, 0), # Red
    (0, 255, 0), # Green
    (0, 0, 255)  # Blue
]
jfc.apply_light_string(lights, 100, ["porch-zone"])

# Print the current state of all zones
for name, state in jfc.get_zone_states().items():
    pattern = state.file
    brightness = state.data.runData.brightness
    colors = state.data.colors
    print(f"Zone '{name}' is {'on' if state.is_on else 'off'} (pattern: '{pattern}', colors: {colors}, brightness: {brightness})")

# Turn off all zones
jfc.turn_off()

# Turn on the 'front-zone' zone - the lights will be in the same state as when they were last on
jfc.turn_on(['front-zone'])

# Retrieve a pattern configuration
config = jfc.get_pattern_config("Colors/Green")
print(config)

# Customize the pattern configuration and run it on the 'front-zone' zone
config.colors.extend([(0, 0, 0)])
config.type = "Chase"
config.direction = "Center"
config.spaceBetweenPixels = 8
config.effectBetweenPixels = "Progression"
config.runData.speed = 1
jfc.apply_pattern_config(config, ["front-zone"])
```

## Contributing

Contributions are welcome! To run the test suite, first set the `JF_TEST_HOST` environment variable to your local JellyFish Lighting controller's address. Then run:

```
python -m pytest ./tests
```

If you don't have a local controller to test with you can skip the integration tests by running:

```
python -m pytest ./tests/unit
```
