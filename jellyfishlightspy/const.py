import logging

LOGGER = logging.getLogger(__package__)
LOGGER.addHandler(logging.NullHandler())

ZONE_DATA = "zones"
PATTERN_DATA = "patternFileList"
PATTERN_CONFIG_DATA = "patternFileData"
STATE_DATA = "runPattern"

VALID_TYPES = ["Color", "Chase", "Paint", "Stacker", "Sequence", "Multi-Paint", "Soffit"]
VALID_DIRECTIONS = ["Left", "Center", "Right"]
VALID_EFFECTS_BETWEEN_PIXELS = ["No Color Transform", "Repeat", "Progression", "Fade", "Fill with Black"]
VALID_EFFECTS = ["No Effect", "Twinkle", "Lightning"]

DEFAULT_TIMEOUT = 10