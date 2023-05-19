import time
from threading import Lock
from typing import Dict, List, Optional, Generic, TypeVar
from .helpers import TimelyEvent, copy
from .model import FirmwareVersion, TimeConfig, ZoneConfig, ZoneState, Pattern, PatternConfig, ScheduleEvent

T = TypeVar('T')

class CacheEntry(Generic[T]):
    """A single entry within the data cache. Contains a data object and event to notify when updates occur"""

    def __init__(self, data: Optional[T] = None):
        self._data = data
        self.event = TimelyEvent()

    @property
    def data(self) -> T:
        """
        The data stored within the cache entry.
        Returns a copy to avoid users inadvertently editing the cache by changing the object's properties
        """
        return copy(self._data)

    @data.setter
    def data(self, data: T) -> None:
        self._data = data
        self.event.trigger()


SINGLE_ENTRY_KEY = "__single_entry__"

class DataCache(Generic[T]):
    """
    Ensures thread safe reads and writes of cached data of a specific type (e.g. zone states), and
    triggers events when data is updated.
    Cache entries are stored in a dict that maps the entry key (a string) to the CacheEntry object.
    """

    def __init__(self):
        self.__data: Dict[str, CacheEntry[T]] = {}
        self.__lock = Lock()
        self.__finalized = TimelyEvent()

    def __repr__(self):
        return self.__class__.__name__ + str({"type": T, "size": self.size})

    def __get_or_create_entry(self, entry_key: str) -> CacheEntry[T]:
        """Retrieves an entry in a non-thread-safe manner, or creates it if it doesn't exist"""
        if entry_key not in self.__data:
            self.__data[entry_key] = CacheEntry()
        return self.__data[entry_key]

    @property
    def size(self) -> int:
        """The current number of entries stored in the cache"""
        return len(self.__data)

    def get_entry(self, entry_key: str=SINGLE_ENTRY_KEY) -> T:
        """Returns the data for a cache entry (or the sole entry if entry_key is not provided)"""
        with self.__lock:
            entry = self.__data.get(entry_key)
            return entry.data if entry else None

    def get_all_entries(self) -> Dict[str, T]:
        """Returns all cached data in a dict that maps the entry key (a string) to the entry's data"""
        with self.__lock:
            return {k: v.data for k, v in self.__data.items()}

    def update_entry(self, data: T, entry_key: str=SINGLE_ENTRY_KEY) -> None:
        """Updates the data for a single entry (or the sole entry if entry_key is not provided)"""
        with self.__lock:
            self.__get_or_create_entry(entry_key).data = data

    def update_entries(self, entries: Dict[str, T]) -> None:
        """Updates the data for multiple entries as a single transaction and triggers the finalization event when complete"""
        with self.__lock:
            for k, v in entries.items():
                self.__get_or_create_entry(k).data = v
        self.__finalized.trigger()

    def delete_entry(self, entry_key: str) -> None:
        """Deletes an entry and triggers the entry's event"""
        entry = None
        with self.__lock:
            entry = self.__data.get(entry_key)
            if entry:
                del self.__data[entry_key]
                entry.event.trigger()

    def clear(self) -> None:
        """Clears all currently cached data"""
        with self.__lock:
            self.__data.clear()

    def await_update(self, timeout: float, entry_keys: Optional[List[str]] = None) -> bool:
        """Waits for a cache update to occur. If entry_keys is provided, waits until all keys have been updated."""
        start_ts = time.perf_counter()
        entry_keys = entry_keys or [SINGLE_ENTRY_KEY]
        for event in [self.__get_or_create_entry(key).event for key in entry_keys]:
            # We cannot simply wait for each event sequentially because messages can be received simultaneously and out of order.
            # To overcome this, use the TimelyEvent timestamp to check if data has been received since this function was called.
            timeout_remaining = timeout - (time.perf_counter() - start_ts) # Decrement the timeout as we wait for each event
            if not event.wait(timeout=timeout_remaining, after_ts=start_ts):
                return False
        return True

    def await_finalization(self, timeout: float) -> bool:
        """
        Waits for finalization of a cache after multiple related updates.
        Used when listeners of cache events need to wait until a multi-update transaction is finished and
        the entity keys are not known in advance.
        """
        return self.__finalized.wait(timeout=timeout)


class JellyFishCache:
    """Responsible for caching all data received from the controller and coordinating data access"""

    def __init__(self):
        self.name_data: DataCache[str] = DataCache()
        self.hostname_data: DataCache[str] = DataCache()
        self.firmware_version_data: DataCache[FirmwareVersion] = DataCache()
        self.time_config_data: DataCache[TimeConfig] = DataCache()
        self.zone_config_data: DataCache[ZoneConfig] = DataCache()
        self.zone_state_data: DataCache[ZoneState] = DataCache()
        self.pattern_list_data: DataCache[Pattern] = DataCache()
        self.pattern_config_data: DataCache[PatternConfig] = DataCache()
        self.calendar_schedule_data: DataCache[List[ScheduleEvent]] = DataCache()
        self.daily_schedule_data: DataCache[List[ScheduleEvent]] = DataCache()