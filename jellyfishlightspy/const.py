import logging

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

ZONE_DATA = "zones"
PATTERN_LIST_DATA = "patternFileList"
RUN_PATTERN_DATA = "runPattern"

DEFAULT_TIMEOUT = 10