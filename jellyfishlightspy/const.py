import logging

LOGGER = logging.getLogger(__package__)
LOGGER.addHandler(logging.NullHandler())

FIRMWARE_VERSION_DATA = "version"
HOSTNAME_DATA = "hostName"
NAME_DATA = "ctlrName"
TIME_CONFIG_DATA = "timeConfig"
ZONE_CONFIG_DATA = "zones"
ZONE_STATE_DATA = "runPattern"
PATTERN_LIST_DATA = "patternFileList"
PATTERN_CONFIG_DATA = "patternFileData"
DELETE_PATTERN_DATA = "patternFileDelete"
SCHEDULE_DATA = "schedule"
CALENDAR_SCHEDULE_DATA = "scheduleCalendar"
DAILY_SCHEDULE_DATA = "scheduleDaily"

VALID_TYPES = ["Color", "Chase", "Paint", "Stacker", "Sequence", "Multi-Paint", "Soffit"]
VALID_DIRECTIONS = ["Left", "Center", "Right"]
VALID_EFFECTS_BETWEEN_PIXELS = ["No Color Transform", "Repeat", "Progression", "Fade", "Fill with Black"]
VALID_EFFECTS = ["No Effect", "Twinkle", "Lightning"]

VALID_ACTION_TYPES = ["RUN", "STOP"]
VALID_START_FROMS = ["sunrise", "sunset", "time"]
VALID_DAYS = ["M", "T", "W", "TH", "F", "SA", "S"]

DEFAULT_TIMEOUT = 10