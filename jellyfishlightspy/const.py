import logging

LOGGER = logging.getLogger(__package__)
LOGGER.addHandler(logging.NullHandler())

ZONE_DATA = "zones"
PATTERN_DATA = "patternFileList"
STATE_DATA = "runPattern"

DEFAULT_TIMEOUT = 10