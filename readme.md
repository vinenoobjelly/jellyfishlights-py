Python api wrapper for JellyFish Lights

~~The hope is to make this a pip installable package~~ 
Now available through pypi/pip!

To install:
- pip install jellyfishslight-py

**Current capabalilities**: 
- Connects to a local JellyFish Lighting controller over websocket
- Retrieve and store the following data:
    - Zones
    - Pattern Files
- Turn on and off controller lights
- Play a pattern
- Set any lights you want

**Example**:
```python
from jellyfishlightspy import *

controllerIP = "192.168.0.245"

#We set the printJSON parameter to true to see the JSON sent to and recieved from the controller
jfc = JellyFishController(controllerIP, True)
jfc.connectAndGetData()
jfc.turnOff()

lights = LightString()
#add red light
lights.add(Light(255, 0, 0))
#add green light
lights.add(Light(0, 255, 0))
#add blue light
lights.add(Light(0, 0, 255))

#Currently all commands that could turn on the lights themselves
#  have an optional zones parameter. If not filled the api wrapper
#  will fill it with all the zones it got from the controller
jfc.sendLightString(lights, ["Zone"])

```
