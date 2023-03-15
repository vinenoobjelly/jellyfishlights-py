import pytest
import os
from typing import List
from jellyfishlightspy import JellyFishController
from tests.helpers import Helpers

@pytest.fixture
def helpers() -> Helpers:
    return Helpers

@pytest.fixture
def controller_host() -> str:
    env = os.environ.get("JF_TEST_HOST")
    if not env:
        raise pytest.UsageError("Required variable for integration testing is unset: JF_TEST_HOST")
    return env

@pytest.fixture
def controller(controller_host) -> JellyFishController:
    jfc = JellyFishController(controller_host)
    jfc.connect()
    yield jfc
    # Cleanup resources after tests
    jfc.turn_off()
    jfc.disconnect()