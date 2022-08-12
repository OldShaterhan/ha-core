"""Platform for the opengarage.io sensor component."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..sensor import SensorEntity

# from .const import DOMAIN

ICON = "mdi:train"
SCAN_INTERVAL = timedelta(minutes=2)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the HAFAS sensor platform."""

    async_add_entities([SensorEntity()], True)


class HafasSensor(SensorEntity):
    """Implementation of a HAFAS sensor."""

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return ICON
