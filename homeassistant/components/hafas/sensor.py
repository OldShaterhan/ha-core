"""Platform for the opengarage.io sensor component."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from pyhafas import HafasClient
from pyhafas.types.fptf import Leg, Station

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from ..sensor import SensorEntity
from .const import DOMAIN

ICON = "mdi:train"
SCAN_INTERVAL = timedelta(minutes=2)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the HaFAS sensor platform."""

    hafas_client: HafasClient = hass.data[DOMAIN][entry.entry_id]

    # print(json.dumps(list(entry.data.keys())))

    # init does not allow async methods - moved earlier
    start_station = (
        await hass.async_add_executor_job(
            hafas_client.locations, entry.data["start_station_id"]
        )
    )[0]
    destination_station = (
        await hass.async_add_executor_job(
            hafas_client.locations, entry.data["destination_station_id"]
        )
    )[0]
    async_add_entities(
        [
            HafasSensor(
                hass,
                hafas_client,
                start_station,
                destination_station,
                entry.data["only_direct"],
            )
        ],
        True,
    )


class HafasSensor(SensorEntity):
    """Implementation of a HaFAS sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: HafasClient,
        start_station: Station,
        destination_station: Station,
        only_direct: bool,
    ) -> None:
        """Initialize the sensor."""
        self._name = f"{start_station.name} to {destination_station.name}"
        self.data = HafasService(
            client, start_station, destination_station, only_direct
        )
        self._state = None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the icon for the frontend."""
        return ICON

    @property
    def native_value(self):
        """Return the departure time of the next train."""
        print("Test")
        print(str(self._state))
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        connections = self.data.connections[0]
        if len(self.data.connections) > 1:
            connections["next"] = self.data.connections[1]["departure"]
        if len(self.data.connections) > 2:
            connections["next_on"] = self.data.connections[2]["departure"]
        return connections

    def update(self):
        """Get the latest delay from HaFAS and updates the state."""
        self.data.update()
        self._state = f"{self.data.connections[0].get('departure', 'Unknown')}"
        if (
            self.data.connections[0].get("delay", 0) != timedelta(0)
            and self.data.connections[0].get("delay", 0) is not None
        ):
            self._state += f" + {str(self.data.connections[0]['delay'])}"


class HafasService:
    """Pull data from HaFAS services."""

    def __init__(
        self,
        client: HafasClient,
        start_station: Station,
        destination_station: Station,
        only_direct: bool,
        offset: timedelta = timedelta(minutes=0),
    ) -> None:
        """Initialize the service."""
        self.start_station = start_station
        self.destination_station = destination_station
        self.only_direct = only_direct
        self.client = client
        self.offset = offset
        self.connections: list[Any] = []

    def update(self) -> None:
        """Update the connection data."""
        print("Update connection data")

        if self.only_direct:
            max_changes = 0
        else:
            max_changes = -1

        all_connections = self.client.journeys(
            origin=self.start_station.id,
            destination=self.destination_station.id,
            date=dt_util.as_local(dt_util.utcnow() + self.offset),
            max_changes=max_changes,
        )
        print("Update works!")

        if not all_connections:
            all_connections = []

        for con in all_connections:
            # print(json.dumps(type(con)))
            connection = vars(con)
            # print(json.dumps(list(connection.keys()), default=str))
            # leg = getattr(con, "legs")[0]
            leg: Leg = connection["legs"][0]
            connection["name"] = leg.name
            connection["cancelled"] = leg.cancelled
            connection["departure"] = leg.departure
            connection["arrival"] = leg.arrival
            connection["delay_arrival"] = leg.arrivalDelay
            connection["delay"] = leg.departureDelay
            connection["ontime"] = leg.arrivalDelay == timedelta(minutes=0)
            connection.pop("legs")

            self.connections.append(connection)
