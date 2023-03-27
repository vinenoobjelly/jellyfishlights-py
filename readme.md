# Python wrapper for JellyFish Lights web socket API

Now available through pypi/pip!

To install:

```
pip install jellyfishlights-py
```

## Current capabalilities

- Connect to a local JellyFish Lighting controller over websocket
- Retrieve the following data:
  - Controller's name, hostname, and firmware version
  - Timezone configuration
  - Zone configuration
  - Preset patterns and their configurations
  - Zone states
  - Calendar schedule
  - Daily schedule
- Turn zones on and off
- Activate a preset pattern
- Set lights to a solid color with brightness control
- Set any individual lights you want with brightness control
- Activate a custom pattern configuration
- Create, update, and delete custom pattern configurations
- Create, update, and delete schedule events (calendar and daily)
- Create, update, and delete zone configurations
- Set the controller's name

## Examples

The snippets below show most of what this module can do and have important usage notes in the comments.

### Connectivity, logging, and basic controller information

```python
from jellyfishlightspy import JellyFishController, ScheduleEvent, ScheduleEventAction, ZoneConfig, PortMapping
import logging

# Debug logging exposes the JSON messages sent to and received from the controller
logging.basicConfig(level = logging.DEBUG)

# Create a controller object and connect
jfc = JellyFishController('192.168.0.245') # hostname also works
jfc.connect()

# Print the controller's name and hostname
print(f"Connected to JellyFish Lighting controller '{jfc.name}' ({jfc.hostname})")

# Print the controller's firmware version information
print(f"Firmware version: {jfc.firmware_version}")

# Print the controller's timezone configuration
print(f"Timezone configuration: {jfc.time_config}")

# Change the controller's user-defined name
jfc.set_name("My JellyFish Controller")

# Disconnect from the controller
jfc.disconnect()
```

### Zones (state, turning on/off, and configuration)

```python
# Print the currently configured zones
# NOTE: all attributes on the controller will return cached data when available.
# If you want to ensure you are retrieving the latest information from the controller,
# use the corresponding get_* function (jfc.get_zone_names() in this case)
print(f"Zones: {jfc.zone_names}")

# Print the current state of all zones
for name, state in jfc.get_zone_states().items():
    pattern = state.file
    brightness = state.data.runData.brightness
    colors = state.data.colors
    print(f"Zone '{name}' is {'on' if state.is_on else 'off'} (pattern: '{pattern}', colors: {colors}, brightness: {brightness})")

# Turn off all zones
# NOTE: Many commands have an optional zones parameter. If not filled, it defaults to all zones
# NOTE: Many of the commands have an optional sync parameter.
# If sync=False (default is True) it sends the command and does not wait for a response (returns immediately)
jfc.turn_off(sync=False)

# Turn on the 'front-zone' zone - the lights will be in the same state as when they were last on
# NOTE: Many of the commands have an optional timeout parameter.
# If sync=True (it is by default), the command is synchronous and will raise a JellyFishException
# if a response isn't received within the timeout period (default is 10 seconds).
jfc.turn_on(["front-zone"], timeout=5)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# !!ADVANCED!! - change zone configurations
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
orig_zones = jfc.zone_configs

# Print current zone configurations
for zone, config in orig_zones.items():
  print(f"Zone '{zone}' config: {config}")

# Add a new zone
new_config = ZoneConfig([
    # NOTE: the phyPort attribute maps as such to the ports on the controller (controller port->phyPort): 1->1, 2->2, 3->4, 4->8
    # NOTE: zoneRGBStartIdx defaults to phyStartIdx. Setting it to the phyEndIdx value will reverse the direction
    # NOTE: ctlrName defaults to the hostname of the controller you are currently connected to (jfc.hostname)
    # NOTE: All of the *Idx values are one less than what is displayed in the app! (e.g. a "1" value in the app is a "0" value here)
    PortMapping(phyPort=1, phyStartIdx=0, phyEndIdx=10, zoneRGBStartIdx=10, ctlrName="JellyFish-XXXX.local"),
    # NOTE: this is the short version that sets only the required fields: phyPort, phyStartIdx, and phyEndIdx
    PortMapping(2, 0, 99)
])
jfc.add_zone("My new zone", new_config)

# Delete the zone we just created
jfc.delete_zone("My new zone")

# Save the full set of all zone configurations at once
jfc.set_zone_configs({"My new zone": new_config}) # This would result in a single zone (any other zones would be deleted)
jfc.set_zone_configs({}) # This would delete all zone configurations
jfc.set_zone_configs(orig_zones) # This would restore the zone configurations to what we retrieved above (before we modified them)
```

### Patterns

```python
# Print the list of currently configured patterns
print(f"Patterns: {jfc.pattern_names}")

# Run a preset pattern on all zones
jfc.apply_pattern("Special Effects/Red Waves")

# Retrieve a pattern configuration
config = jfc.get_pattern_config("Colors/Blue")
print(config)

# Customize the pattern configuration and run it on the 'front-zone' zone
# (this example shows just a few of the configurable pattern attributes)
config.colors.extend([0, 0, 0]) # Note that 'colors' is a list of ints, not a list of tuples! Be sure the list is divisible by 3
config.type = "Chase" # Valid values: ["Color", "Chase", "Paint", "Stacker", "Sequence", "Multi-Paint", "Soffit"]
config.direction = "Center" # Valid values: ["Left", "Center", "Right"]
config.spaceBetweenPixels = 8
config.effectBetweenPixels = "Progression" # Valid values: ["No Color Transform", "Repeat", "Progression", "Fade", "Fill with Black"]
config.runData.speed = 1
config.runData.effect = "No Effect" # Valid values: ["No Effect", "Twinkle", "Lightning"]
jfc.apply_pattern_config(config, ["front-zone"])

# Save your new pattern to a file to easily run later.
# The parent folder will be created if it doesn't exist.
# You can also update existing patterns this way (if they're editable).
jfc.save_pattern("Special Effects/Blue Waves", config)

# Delete the pattern
jfc.delete_pattern("Special Effects/Blue Waves")
```

### Manual light control

```python
# Set 'front-zone' and 'back-zone' to a solid color (white @ 100% brightness in this case)
jfc.apply_color((255, 255, 255), 100, ["front-zone", "back-zone"])

# Set individual lights on the 'porch-zone' zone
# This example sets only the first 3 lights in the zone, but you can set as many as you would like
lights = [
    (255, 0, 0), # Red
    (0, 255, 0), # Green
    (0, 0, 255)  # Blue
]
jfc.apply_light_string(lights, 75, ["porch-zone"]) # 75% brightness
```

### Schedules

```python
# Retrieve the calendar schedule
orig_events = jfc.calendar_schedule # Use jfc.daily_schedule to get the daily schedule
for event in orig_events:
  print(event)

# Add an event to the schedule
event = ScheduleEvent(
    # Must be in YYYYMMDD format for calendar events
    # Even though a year must be specified the event will run annually
    # You must include each individual day if specifying a range
    days = ["20231231", "20230101", "20230102"],
    # days = ["M", "T", "W", "TH", "F", "SA", "S"], <-- Example for a daily schedule event
    actions = [
        ScheduleEventAction(
          type = "RUN",
          startFrom = "sunset",
          hour = 0, # For 'sunrise' and 'sunset', hour must be 0...
          minute = 30, # ...and the minute offset must be between -55 and 55 and divisible by 5
          patternFile = "Special Effects/Rainbow Waves",
          zones = jfc.zone_names # The list of zones for each RUN/STOP action must match!
        ),
        # For 'time', the hour must be between 0 and 23, and minute between 0 and 59
        ScheduleEventAction("STOP", "time", 5, 00, "", jfc.zone_names)
    ]
)
jfc.add_calendar_event(event)

# To remove events you must send the updated full schedule of events
jfc.set_calendar_schedule([event]) # This would delete all events other than what we just created
jfc.set_calendar_schedule([]) # This would delete all events
jfc.set_calendar_schedule(orig_events) # This would restore the schedule to what we retrieved above (before we modified it)

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
