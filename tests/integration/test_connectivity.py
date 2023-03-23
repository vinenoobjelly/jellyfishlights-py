import pytest
import traceback
from jellyfishlightspy import JellyFishController, JellyFishException

def test_connect(controller_host):
    jfc = JellyFishController(controller_host)
    with pytest.raises(JellyFishException) as e:
        jfc.pattern_list
        assert "Not connected" in str(e)
    jfc.connect()
    assert jfc.connected
    assert len(jfc.pattern_list) > 0
    jfc.disconnect()
    assert not jfc.connected
    assert len(jfc.pattern_list) > 0 # now uses cached results
    with pytest.raises(JellyFishException) as e:
        jfc.get_pattern_list()
        assert "Not connected" in str(e)

def test_bad_host():
    jfc = JellyFishController("bad-controller-host")
    with pytest.raises(JellyFishException) as e:
        jfc.connect()
        assert "Could not connect" in str(e)

def test_timeout():
    jfc = JellyFishController("bad-controller-host")
    with pytest.raises(JellyFishException) as e:
        jfc.connect(timeout=1)
        assert "timed out" in str(e)