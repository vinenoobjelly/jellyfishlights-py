import pytest
import traceback
from jellyfishlightspy import JellyFishController, JellyFishLightsException

def test_connect(controller_host):
    jfc = JellyFishController(controller_host)
    with pytest.raises(JellyFishLightsException) as e:
        jfc.get_patterns()
        assert "Not connected" in str(e)
    jfc.connect()
    assert jfc.connected
    jfc.disconnect()
    assert not jfc.connected
    with pytest.raises(JellyFishLightsException) as e:
        jfc.get_patterns()
        assert "Not connected" in str(e)

def test_bad_host():
    jfc = JellyFishController("bad-controller-host")
    with pytest.raises(JellyFishLightsException) as e:
        jfc.connect()
        assert "Could not connect" in str(e)

def test_timeout():
    jfc = JellyFishController("bad-controller-host")
    with pytest.raises(JellyFishLightsException) as e:
        jfc.connect(timeout=0)
        assert "timed out" in str(e)