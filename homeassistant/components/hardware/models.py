"""Models for Hardware."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from homeassistant.core import HomeAssistant, callback


@dataclass
class BoardInfo:
    """Board info type."""

    hassio_board_id: str | None
    manufacturer: str
    model: str | None
    revision: str | None


@dataclass(frozen=True)
class USBInfo:
    """USB info type."""

    vid: str
    pid: str
    serial_number: str | None
    manufacturer: str | None
    description: str | None


@dataclass(frozen=True)
class HardwareInfo:
    """Hardware info type."""

    name: str | None
    board: BoardInfo | None
    dongles: list[USBInfo] | None
    url: str | None


class HardwareProtocol(Protocol):
    """Define the format of hardware platforms."""

    @callback
    def async_info(self, hass: HomeAssistant) -> HardwareInfo:
        """Return info."""
