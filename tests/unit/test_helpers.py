import pytest
import time
from threading import Thread
from jellyfishlightspy.helpers import TimelyEvent

# Note: tests in model.py sufficiently cover from_json, to_json, _default, and _object_hook

def test_timely_event():
    event = TimelyEvent()
    assert not event.is_set()
    event.set()
    assert event.is_set()
    event.clear()
    assert not event.is_set()
    thread = Thread(target=lambda: event.wait(timeout=1), daemon=True)
    thread.start()
    time.sleep(.1)
    assert thread.is_alive()
    event.set()
    thread.join(timeout=.1)
    assert not thread.is_alive()
    start = time.perf_counter()
    event.trigger()
    assert not event.is_set()
    thread = Thread(target=lambda: event.wait(after_ts=start, timeout=1), daemon=True)
    thread.start()
    thread.join(timeout=.1)
    assert not thread.is_alive()
