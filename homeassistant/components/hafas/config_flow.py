"""Config flow for HaFAS integration."""
from __future__ import annotations

import logging
from typing import Any

from pyhafas import HafasClient
from pyhafas.profile import DBProfile
from pyhafas.types.fptf import Station
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("start_station"): str,
        vol.Required("destination_station"): str,
        vol.Required("only_direct"): bool,
    }
)


def validate_station(station: str) -> Station:
    """Try to get station based on the user input."""

    client = HafasClient(DBProfile(), debug=True)
    res = client.locations(station)
    if res.count == 0:
        return None
    return res[0]


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TO-DO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    start_station = await hass.async_add_executor_job(
        validate_station, data["start_station"]
    )

    destination_station = await hass.async_add_executor_job(
        validate_station, data["destination_station"]
    )

    # hub = PlaceholderHub(data["host"])

    # if not await hub.authenticate(data["username"], data["password"]):
    #     raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    data["start_station_id"] = start_station.id
    data["destination_station_id"] = destination_station.id
    data["start_station_name"] = start_station.name
    data["destination_station_name"] = destination_station.name

    # Return info that you want to store in the config entry.
    return {
        "title": f"{start_station.name} to {destination_station.name}",
        "start_station_name": start_station.name,
        "destination_station_name": destination_station.name,
        "start_station_id": start_station.id,
        "destination_station_id": destination_station.id,
        "only_direct": data["only_direct"],
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HaFAS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
