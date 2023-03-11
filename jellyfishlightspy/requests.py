from typing import List, Optional
from types import SimpleNamespace
from .model import StateData, RunPatternData

class GetDataRequest:

    def __init__(self, get: List[str]) -> None:
        self.cmd = 'toCtlrGet'
        self.get = [get]

class RunPatternRequest:

    def __init__(self, state: int, zoneName: List[str], file: str = "", id: str = "", data: Optional[RunPatternData] = None):
        self.cmd = 'toCtlrSet'
        self.runPattern = vars(StateData(state=state, zoneName=zoneName, file=file, id=id, data=data))