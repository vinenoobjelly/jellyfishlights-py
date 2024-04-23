import pytest
from mock import Mock
from typing import List
from jellyfishlightspy import JellyFishController
from tests.helpers import Helpers

def test_listener(controller):
    on_open = Mock()
    on_close = Mock()
    on_message = Mock()
    on_error = Mock()
    controller.add_listener(on_open, on_close, on_message, on_error)
    assert controller.connected
    controller.disconnect()
    on_close.assert_called_once()
    controller.connect()
    on_open.assert_called_once()
    controller.get_name()
    on_message.assert_called_once()