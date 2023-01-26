Python api wrapper for JellyFish Lights

~~The hope is to make this a pip installable package~~ 
Now available through pypi/pip!

To install:
- pip install jellyfishlights-py

**Current capabalilities**: 
- Connects to a local JellyFish Lighting controller over websocket
- Retrieves and stores the following data:
    - Zones
    - Pattern Files
    - Active Run Pattern for a Zone
- Turns on and off controller lights
- Plays a pattern
- Sets lights to a solid color with brightness control
- Set any individual lights you want

**Example**:
```python
from jellyfishlightspy import *

controllerIP = "192.168.0.245"

# We set the printJSON parameter to true to see the JSON sent to and recieved from the controller
jfc = JellyFishController(controllerIP, True)
jfc.connectAndGetData()
jfc.turnOff()

lights = LightString()
# Add red light
lights.add(Light(255, 0, 0))
# Add green light
lights.add(Light(0, 255, 0))
# Add blue light
lights.add(Light(0, 0, 255))

# Currently all commands that could turn on the lights themselves
# have an optional zones parameter. If not filled the api wrapper
# will fill it with all the zones it got from the controller
jfc.sendLightString(lights, ["Zone"])

# Play a pre-saved pattern on all zones
jfc.playPattern('Special Effects/Red Waves')
rpd = jfc.getRunPattern("Zone")
print(f"Zones is {'on' if rpd.state else 'off'} (pattern: '{rpd.file}')")

# Set all zones to a solid color (white @ 100% brightness in this case)
jfc.sendColor((255, 255, 255), 100)
```
