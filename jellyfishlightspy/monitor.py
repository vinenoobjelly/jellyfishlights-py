
import time
from threading import Event
from typing import Dict, List, Optional, Callable
from .cache import JellyFishCache
from .helpers import JellyFishException, from_json
from .model import Pattern, RunConfig, PatternConfig, ZoneState, ZoneConfig, FirmwareVersion, ScheduleEvent
from .const import (
    LOGGER,
    NAME_DATA,
    HOSTNAME_DATA,
    FIRMWARE_VERSION_DATA,
    TIME_CONFIG_DATA,
    ZONE_CONFIG_DATA,
    PATTERN_LIST_DATA,
    PATTERN_CONFIG_DATA,
    ZONE_STATE_DATA,
    DEFAULT_TIMEOUT,
    DELETE_PATTERN_DATA,
    SCHEDULE_DATA,
)

class WebSocketMonitor:
    """
    Responsible for listening to web socket events (connect, message, error, disconnect), parsing messages,
    and updating the data cache.
    """

    def __init__(self, address: str, cache: JellyFishCache):
        self.__address = address
        self.__cache = cache
        self.__connected = Event()
        self.__open_listeners = []
        self.__close_listeners = []
        self.__message_listeners = []
        self.__error_listeners = []

    def __repr__(self):
        return self.__class__.__name__ + str({"address": self.__address, "connected": self.connected})

    @property
    def connected(self) -> bool:
        """Returns true if the the web socket connection to the controller is established"""
        return self.__connected.is_set()

    def add_listener(self, on_open:Callable=None, on_close:Callable=None, on_message:Callable=None, on_error:Callable=None) -> None:
        """Add listeners to respond to web socket events"""
        if on_open:
            self.__open_listeners.append(on_open)
        if on_close:
            self.__close_listeners.append(on_close)
        if on_message:
            self.__message_listeners.append(on_message)
        if on_error:
            self.__error_listeners.append(on_error)

    def await_connection(self, timeout: float) -> None:
        """Waits for a connection to the controler to be established. Raises a JellyFishException upon timeout"""
        return self.__connected.wait(timeout=timeout)

    def on_open(self, ws):
        """Callback method that is invoked when the web socket connection is opened"""
        LOGGER.debug("Connected to the JellyFish Lighting controller at %s", self.__address)
        self.__connected.set()
        [l() for l in self.__open_listeners]

    def on_close(self, ws, status, message):
        """Callback method that is invoked when the web socket connection is closed"""
        LOGGER.debug("Disconnected from the JellyFish Lighting controller at %s", self.__address)
        self.__connected.clear()
        [l(status, message) for l in self.__close_listeners]

    def on_error(self, ws, error):
        """Callback method that is invoked when the web socket connection encounters an error"""
        LOGGER.error("Web socket connection to the JellyFish Lighting controller at %s encountered an error: %s", self.__address, error)
        [l(error) for l in self.__error_listeners]

    def on_message(self, ws, message):
        """Callback method that is invoked when data is received over the web socket connection"""
        LOGGER.debug("Recieved: %s", message)
        try:
            # Parse the data
            data = from_json(message)
            if data["cmd"] != "fromCtlr":
                return

            # Check what type of data the message contains and update cached data
            if NAME_DATA in data:
                ctlr_name = data[NAME_DATA]
                self.__cache.name_data.update_entry(ctlr_name)

            elif HOSTNAME_DATA in data:
                hostname = data[HOSTNAME_DATA]
                self.__cache.hostname_data.update_entry(hostname)

            elif FIRMWARE_VERSION_DATA in data:
                data = data[FIRMWARE_VERSION_DATA]
                self.__cache.firmware_version_data.update_entry(data)

            elif TIME_CONFIG_DATA in data:
                time_config = data[TIME_CONFIG_DATA]
                self.__cache.time_config_data.update_entry(time_config)

            elif ZONE_CONFIG_DATA in data:
                entries = data[ZONE_CONFIG_DATA]
                self.__cache.zone_config_data.update_entries(entries)
                for deleted in list(set(self.__cache.zone_config_data.get_all_entries()) - set(entries)):
                    self.__cache.zone_config_data.delete_entry(deleted)

            elif PATTERN_LIST_DATA in data:
                entries = {str(pattern): pattern for pattern in data[PATTERN_LIST_DATA]}
                self.__cache.pattern_list_data.update_entries(entries)
                for deleted in list(set(self.__cache.pattern_list_data.get_all_entries()) - set(entries)):
                    self.__cache.pattern_list_data.delete_entry(deleted)

            elif ZONE_STATE_DATA in data:
                state = data[ZONE_STATE_DATA]
                entries = {zone: state for zone in state.zoneName}
                self.__cache.zone_state_data.update_entries(entries)

            elif PATTERN_CONFIG_DATA in data:
                data = data[PATTERN_CONFIG_DATA]
                pattern = Pattern(data["folders"], data["name"])
                if pattern.is_folder:
                    return
                config = data["jsonData"]
                self.__cache.pattern_config_data.update_entry(config, str(pattern))
                # Add to the pattern list if it's new
                if self.__cache.pattern_list_data.size > 0 and self.__cache.pattern_list_data.get_entry(str(pattern)) is None:
                    self.__cache.pattern_list_data.update_entry(pattern, str(pattern))

            elif DELETE_PATTERN_DATA in data:
                pattern = data[DELETE_PATTERN_DATA]
                self.__cache.pattern_list_data.delete_entry(str(pattern))
                if not pattern.is_folder:
                    self.__cache.pattern_config_data.delete_entry(str(pattern))

            elif SCHEDULE_DATA in data:
                schedule_type = data[SCHEDULE_DATA]
                events = data["events"]
                if schedule_type == "calendar":
                    self.__cache.calendar_schedule_data.update_entry(events)
                elif schedule_type == "daily":
                    self.__cache.daily_schedule_data.update_entry(events)

            [l(message) for l in self.__message_listeners]

        except Exception:
            LOGGER.exception("Error encountered while processing web socket message: '%s'", message)