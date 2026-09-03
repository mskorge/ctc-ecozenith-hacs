"""Adapter between Home Assistant and the vendored ``ctc_ecozenith`` library.

This is the only module that reaches into ``vendor/``. Swapping the vendored
copy for the ``ctc-ecozenith`` PyPI package later means changing just the
imports below.
"""

from __future__ import annotations

from modbus_connection import ModbusError, ModbusTcpParams
from modbus_connection.tmodbus import ModbusConnection

from .vendor.ctc_ecozenith import (
    HS_SETPOINT_MAX,
    HS_SETPOINT_MIN,
    SETPOINT_STEP,
    AlarmSnapshot,
    CtcEcoZenith,
    software_version,
)
from .vendor.ctc_ecozenith._vendor_version import __version__ as LIBRARY_VERSION

__all__ = [
    "HS_SETPOINT_MAX",
    "HS_SETPOINT_MIN",
    "LIBRARY_VERSION",
    "SETPOINT_STEP",
    "AlarmSnapshot",
    "CtcApiClient",
    "CtcApiError",
    "CtcEcoZenith",
    "build_connection",
    "software_version",
]


class CtcApiError(ModbusError):
    """Raised for any CTC EcoZenith communication failure."""


def build_connection(host: str, port: int) -> ModbusConnection:
    """Create (but do not open) a Modbus TCP connection to the unit."""
    return ModbusConnection(ModbusTcpParams(host=host, port=port))


class CtcApiClient:
    """One :class:`CtcEcoZenith` device bound to one Modbus unit on a connection."""

    def __init__(self, connection: ModbusConnection, unit_id: int) -> None:
        """Bind the client to ``unit_id`` on ``connection``."""
        self._device = CtcEcoZenith(connection.for_unit(unit_id))

    @property
    def device(self) -> CtcEcoZenith:
        """Return the underlying library device object."""
        return self._device

    async def async_probe(self) -> int:
        """Return the controller's product-type register."""
        try:
            return await self._device.async_probe()
        except ModbusError as err:
            raise CtcApiError(str(err)) from err

    async def async_update(self) -> None:
        """Refresh settings and readings."""
        try:
            await self._device.async_update()
        except ModbusError as err:
            raise CtcApiError(str(err)) from err

    async def async_read_alarms(self) -> AlarmSnapshot:
        """Read the alarm / info-text buffers (a separate stateful read)."""
        try:
            return await self._device.async_read_alarms()
        except ModbusError as err:
            raise CtcApiError(str(err)) from err

    async def async_write(self, component: str, field: str, value: object) -> None:
        """Write ``value`` to ``field`` of the named component."""
        try:
            await self._device.async_write(component, field, value)
        except ModbusError as err:
            raise CtcApiError(str(err)) from err
