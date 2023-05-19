import time
from threading import Thread
from jellyfishlightspy.cache import DataCache

def test_data_cache():
    c = DataCache()
    assert len(c.get_all_entries()) == 0
    e1 = ("1", "e1")
    e2 = ("2", ["e", "e"])
    def add_entrys():
        time.sleep(.1)
        c.update_entry(e1[1], e1[0])
        time.sleep(.1)
        c.update_entry(e2[1], e2[0])
    t = Thread(target=add_entrys, daemon=True)
    t.start()
    assert c.await_update(1, [e1[0]])
    assert c.get_entry(e1[0]) == e1[1]
    assert not c.get_entry(e2[0])
    assert c.await_update(1, [e2[0]])
    assert c.get_entry(e2[0]) == e2[1]
    t.join()
    assert len(c.get_all_entries()) == 2
    e2_copy = c.get_entry(e2[0])
    e2_copy.append("e")
    assert len(c.get_entry(e2[0])) == 2
    def delete_entrys():
        time.sleep(.1)
        c.delete_entry(e1[0])
        c.delete_entry(e2[0])
    t = Thread(target=delete_entrys, daemon=True)
    t.start()
    assert c.await_update(1, [e1[0], e2[0]])
    assert len(c.get_all_entries()) == 0
    assert not c.get_entry(e1[0])
    assert not c.get_entry(e2[0])
    t.join()