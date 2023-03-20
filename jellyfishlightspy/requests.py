from typing import List, Optional
from types import SimpleNamespace
from .model import ZoneState, PatternConfig, Pattern

class GetRequest:
    def __init__(self, *args):
        self.cmd = 'toCtlrGet'
        self.get = [[*args]]

class SetStateRequest:
    def __init__(self, state: int, zoneName: List[str], file: str = "", id: str = "", data: Optional[PatternConfig] = None):
        self.cmd = 'toCtlrSet'
        self.runPattern = ZoneState(state = state, zoneName = zoneName, file = file, id = id, data = data)

class SetPatternConfigRequest:
    def __init__(self, pattern: Pattern, jsonData: PatternConfig):
        self.cmd = 'toCtlrSet'
        self.patternFileData = {
            "folders": pattern.folders,
            "name": pattern.name,
            "jsonData": jsonData
        }

class DeletePatternRequest:
    def __init__(self, pattern: Pattern):
        self.cmd = 'toCtlrSet'
        self.patternFileDelete = pattern