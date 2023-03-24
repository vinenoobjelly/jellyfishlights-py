from typing import List, Optional, Dict
from types import SimpleNamespace
from .model import ZoneConfig, ZoneState, PatternConfig, Pattern, ScheduleEvent
from .const import (
    CONTROLLER_VERSION_DATA,
    CONTROLLER_HOSTNAME_DATA,
    ZONE_CONFIG_DATA,
    PATTERN_LIST_DATA,
    PATTERN_CONFIG_DATA,
    ZONE_STATE_DATA,
    CALENDAR_SCHEDULE_DATA,
    DAILY_SCHEDULE_DATA,
)

class GetRequest:
    def __init__(self, *args):
        self.cmd = 'toCtlrGet'
        self.get = [[*args]]


class GetControllerVersionRequest(GetRequest):
    def __init__(self):
        super().__init__(CONTROLLER_VERSION_DATA)


class GetControllerHostnameRequest(GetRequest):
    def __init__(self):
        super().__init__(CONTROLLER_HOSTNAME_DATA)


class GetZoneConfigRequest(GetRequest):
    def __init__(self):
        super().__init__(ZONE_CONFIG_DATA)


class GetPatternListRequest(GetRequest):
    def __init__(self):
        super().__init__(PATTERN_LIST_DATA)


class GetPatternConfigRequest(GetRequest):
    def __init__(self, patterns: List[str]):
        args = []
        for pattern in patterns:
            pobj = Pattern.from_str(pattern)
            args.extend([pobj.folders, pobj.name])
        super().__init__(PATTERN_CONFIG_DATA, *args)


class GetZoneStateRequest(GetRequest):
    def __init__(self, zones: List[str]):
        super().__init__(ZONE_STATE_DATA, *zones)


class GetCalendarScheduleRequest(GetRequest):
    def __init__(self):
        super().__init__(CALENDAR_SCHEDULE_DATA)


class GetDailyScheduleRequest(GetRequest):
    def __init__(self):
        super().__init__(DAILY_SCHEDULE_DATA)


class SetRequest:
    def __init__(self):
        self.cmd = "toCtlrSet"


class SetZoneConfigRequest(SetRequest):
    def __init__(self, zone_configs: Dict[str, ZoneConfig]):
        super().__init__()
        self.save = True
        self.zones = zone_configs


class SetZoneStateRequest(SetRequest):
    def __init__(self, state: int, zoneName: List[str], file: str="", id: str="", data: Optional[PatternConfig]=None):
        super().__init__()
        self.runPattern = ZoneState(state=state, zoneName=zoneName, file=file, id=id, data=data)


class SetPatternConfigRequest(SetRequest):
    def __init__(self, pattern: Pattern, jsonData: PatternConfig):
        super().__init__()
        self.patternFileData = {
            "folders": pattern.folders,
            "name": pattern.name,
            "jsonData": jsonData
        }


class SetCalendarScheduleRequest(SetRequest):
    def __init__(self, events: List[ScheduleEvent]):
        super().__init__()
        self.schedule = "calendar"
        self.events = events


class SetDailyScheduleRequest(SetRequest):
    def __init__(self, events: List[ScheduleEvent]):
        super().__init__()
        self.schedule = "daily"
        self.events = events


class DeletePatternRequest(SetRequest):
    def __init__(self, pattern: Pattern):
        super().__init__()
        self.patternFileDelete = pattern