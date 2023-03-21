
import logging
import time
from threading import Thread, Lock
from typing import Dict, List, Optional, Generic, TypeVar
from .helpers import JellyFishException, TimelyEvent, from_json, copy
from .model import Pattern, RunConfig, PatternConfig, ZoneState, ZoneConfig, ControllerVersion
from .const import (
    LOGGER,
    ZONE_CONFIG_DATA,
    PATTERN_LIST_DATA,
    PATTERN_CONFIG_DATA,
    ZONE_STATE_DATA,
    DEFAULT_TIMEOUT,
    DELETE_PATTERN_DATA,
    CONTROLLER_VERSION_DATA,
)

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
        Returns a copy to avoid users inadvertently changing the object and thereby modifying the cache
        """
        return copy(self._data)

    @data.setter
    def data(self, data: T) -> None:
        self._data = data
        self.event.trigger()


SINGLE_ENTRY_KEY = "__single_entry__"

class DataCache(Generic[T]):
    """
    Ensures thread safe reads and writes of cached data, and triggers events when data is updated.
    Cache entries are stored in a dict that maps the entry key (a string) to the CacheEntry object.
    """

    def __init__(self):
        self.__data: Dict[str, CacheEntry[T]] = {}
        self.__lock = Lock()
        self.__finalized = TimelyEvent()

    def __repr__(self):
        return self.__class__.__name__ + str({"type": T, "entries": len(self.__data)})

    def __get_or_create_entry(self, entry_key: str) -> CacheEntry[T]:
        """Retrieves an entry in a non-thread-safe manner, or creates it if it doesn't exist"""
        if entry_key not in self.__data:
            self.__data[entry_key] = CacheEntry()
        return self.__data[entry_key]

    def get_entry(self, entry_key: str=SINGLE_ENTRY_KEY) -> T:
        """Returns the data for a single entry"""
        with self.__lock:
            entry = self.__data.get(entry_key)
            return entry.data if entry else None

    def get_all_entries(self) -> Dict[str, T]:
        """Returns all cached data in a dict that maps the entry key (a string) to the entry's data"""
        with self.__lock:
            return {k: v.data for k, v in self.__data.items()}

    def update_entry(self, data: T, entry_key: str=SINGLE_ENTRY_KEY) -> None:
        """Updates the data for a single entry"""
        with self.__lock:
            self.__get_or_create_entry(entry_key).data = data

    def update_entries(self, entries: Dict[str, T]) -> None:
        """Updates the data for multiple entries as a single transaction and triggers the finalization event"""
        with self.__lock:
            for k, v in entries.items():
                self.__get_or_create_entry(k).data = v
        self.__finalized.trigger()

    def delete_entry(self, entry_key: str) -> None:
        """Deletes an entry and triggers the entry's event"""
        entry = self.__data.get(entry_key)
        if entry:
            with self.__lock:
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

class WebSocketMonitor:
    """
    Responsible for listening to web socket events (connect, message, error, disconnect), parsing &
    caching data, and notifying the main thread (i.e. JellyFishController) when new data is available.
    """

    def __init__(self, address: str):
        self.__address = address
        self.__connected: TimelyEvent = TimelyEvent()
        self.__controller_version_cache: DataCache[ControllerVersion] = DataCache()
        self.__zone_config_cache: DataCache[ZoneConfig] = DataCache()
        self.__zone_state_cache: DataCache[ZoneState] = DataCache()
        self.__pattern_list_cache: DataCache[List[Pattern]] = DataCache()
        self.__pattern_config_cache: DataCache[PatternConfig] = DataCache()

    def __repr__(self):
        return self.__class__.__name__ + str({"address": self.__address, "connected": self.connected})

    @property
    def connected(self) -> bool:
        """Returns true if the the web socket connection to the controller is established"""
        return self.__connected.is_set()

    @property
    def controller_version(self) -> ControllerVersion:
        """The controllers version information"""
        return self.__controller_version_cache.get_entry()

    @property
    def zone_configs(self) -> Dict[str, ZoneConfig]:
        """The current zones and their configuration. Ensures thread safe access via Locks"""
        return self.__zone_config_cache.get_all_entries()

    @property
    def pattern_list(self) -> Dict[str, Pattern]:
        """The list of preset patterns currently available. Ensures thread safe access via Locks"""
        return self.__pattern_list_cache.get_all_entries()

    @property
    def pattern_configs(self) -> Dict[str, PatternConfig]:
        """The pattern configurations currently available. Ensures thread safe access via Locks"""
        return self.__pattern_config_cache.get_all_entries()

    @property
    def zone_states(self) -> Dict[str, ZoneState]:
        """The state of each zone. Ensures thread safe access via Locks"""
        return self.__zone_state_cache.get_all_entries()

    def await_connection(self, timeout: float) -> None:
        """Waits for a connection to the controler to be established. Raises a JellyFishException upon timeout"""
        if not self.__connected.wait(timeout=timeout):
            raise JellyFishException(f"Connection to controller at {self.__address} timed out")

    def await_controller_version_data(self, timeout: float) -> None:
        """Waits for new zone data to be received from the controller. Raises a JellyFishException upon timeout"""
        if not self.__controller_version_cache.await_update(timeout):
            raise JellyFishException("Request for controller version information timed out")

    def await_zone_config_data(self, timeout: float) -> None:
        """Waits for new zone data to be received from the controller. Raises a JellyFishException upon timeout"""
        if not self.__zone_config_cache.await_finalization(timeout):
            raise JellyFishException("Request for zone config data timed out")

    def await_pattern_list_data(self, timeout: float, patterns: Optional[List[str]] = None) -> None:
        """
        Waits for new pattern list data to be received from the controller. Raises a JellyFishException upon timeout.
        If patterns is provided, waits for specific pattern updates. Currently only used for pattern delete operations.
        """
        if patterns and self.__pattern_list_cache.await_update(timeout, patterns):
            return
        if not patterns and self.__pattern_list_cache.await_finalization(timeout):
            return
        raise JellyFishException("Request for pattern list data timed out")

    def await_zone_state_data(self, timeout: float, zones: List[str]) -> None:
        """Waits for new zone state data to be received from the controller. Raises a JellyFishException upon timeout"""
        if not self.__zone_state_cache.await_update(timeout, zones):
            raise JellyFishException(f"Request for the state data of zones '{zones}' timed out")

    def await_pattern_config_data(self, timeout: float, patterns: List[str]) -> None:
        """Waits for new pattern config data to be received from the controller. Raises a JellyFishException upon timeout"""
        if not self.__pattern_config_cache.await_update(timeout, patterns):
            raise JellyFishException(f"Request for the configuration of patterns '{patterns}' timed out")

    def on_open(self, ws):
        """Callback method that is invoked when the web socket connection is opened"""
        LOGGER.debug("Connected to the JellyFish Lighting controller at %s", self.__address)
        self.__connected.set()

    def on_close(self, ws, status, message):
        """Callback method that is invoked when the web socket connection is closed"""
        LOGGER.debug("Disconnected from the JellyFish Lighting controller at %s", self.__address)
        self.__connected.clear()

    def on_error(self, ws, error):
        """Callback method that is invoked when the web socket connection encounters an error"""
        LOGGER.error("Web socket connection to the JellyFish Lighting controller at %s encountered an error: %s", self.__address, error)

    def on_message(self, ws, message):
        """Callback method that is invoked when data is received over the web socket connection"""
        LOGGER.debug("Recieved: %s", message)
        try:
            # Parse the data
            data = from_json(message)
            if data["cmd"] != "fromCtlr":
                return

            # Check what type of data the message contains (zones, patterns, or states) and update cached data
            if CONTROLLER_VERSION_DATA in data:
                data = data[CONTROLLER_VERSION_DATA]
                self.__controller_version_cache.update_entry(data)

            elif ZONE_CONFIG_DATA in data:
                entries = {zone: config for zone, config in data[ZONE_CONFIG_DATA].items()}
                self.__zone_config_cache.update_entries(entries)

            elif PATTERN_LIST_DATA in data:
                entries = {str(pattern): pattern for pattern in data[PATTERN_LIST_DATA]}
                self.__pattern_list_cache.update_entries(entries)

            elif ZONE_STATE_DATA in data:
                state = data[ZONE_STATE_DATA]
                entries = {zone: state for zone in state.zoneName}
                self.__zone_state_cache.update_entries(entries)

            elif PATTERN_CONFIG_DATA in data:
                data = data[PATTERN_CONFIG_DATA]
                pattern = Pattern(data["folders"], data["name"])
                if not pattern.is_folder:
                    config = data["jsonData"]
                    self.__pattern_config_cache.update_entry(config, str(pattern))
                    self.__pattern_list_cache.update_entry(pattern, str(pattern))

            elif DELETE_PATTERN_DATA in data:
                pattern = data[DELETE_PATTERN_DATA]
                self.__pattern_list_cache.delete_entry(str(pattern))
                if not pattern.is_folder:
                    self.__pattern_config_cache.delete_entry(str(pattern))

        except Exception:
            LOGGER.exception("Error encountered while processing web socket message: '%s'", message)