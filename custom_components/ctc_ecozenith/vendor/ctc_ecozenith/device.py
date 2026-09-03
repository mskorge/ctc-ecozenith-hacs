"""The top-level :class:`CtcEcoZenith` device object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from modbus_connection.model import Component, ComponentGroup

from .alarms import Alarms, AlarmSnapshot
from .control_parameters import ControlParameters
from .readings import Readings
from .settings import Settings

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

__all__ = [
    "MANUFACTURER",
    "MODEL",
    "PRODUCT_TYPE",
    "PROBE_REGISTER",
    "CtcEcoZenith",
    "DeviceInformation",
    "software_version",
]

MANUFACTURER = "CTC"
MODEL = "EcoZenith i360"

# Holding register read by :meth:`CtcEcoZenith.async_probe` - "sProductType".
PROBE_REGISTER = 62253
# TODO: pin the value register 62253 returns on a real i360H, then have the
# config flow assert probe() == PRODUCT_TYPE instead of "any successful read".
PRODUCT_TYPE: int | None = None


@dataclass(frozen=True, slots=True)
class DeviceInformation:
    """Identity of the unit.

    Manufacturer and model are library constants (the BMS interface exposes no
    model/serial register). ``software_version`` is filled in by the caller from
    :func:`software_version` after the first refresh.
    """

    manufacturer: str = MANUFACTURER
    model: str = MODEL
    software_version: str | None = None


def software_version(readings: Readings) -> str | None:
    """Format the display software version from registers 62244 / 62245.

    Returns ``None`` until :meth:`CtcEcoZenith.async_update` has populated the
    readings. Encoding is unverified - treat the result as an opaque label.
    """
    date = readings.display_sw_version_date
    year = readings.display_sw_version_year
    if not date or not year:
        return None
    return f"{year}.{date}"


class CtcEcoZenith:
    """A CTC EcoZenith i360 heat pump / heating system on the BMS Modbus interface.

    Construct it from a :class:`modbus_connection.ModbusUnit`; the caller owns the
    transport. Call :meth:`async_update` to refresh the polled sub-systems in as
    few Modbus reads as possible, then read decoded values off ``settings`` and
    ``readings``. Drive the installation through :meth:`async_write` targeting the
    ``control_parameters`` component (which must be re-asserted every <5 min).
    """

    def __init__(self, unit: ModbusUnit) -> None:
        self._unit = unit
        self.settings = Settings(unit)
        self.readings = Readings(unit)
        self.control_parameters = ControlParameters(unit)
        self.alarms = Alarms(unit)
        self.info = DeviceInformation()
        self._group = ComponentGroup(unit, self._components)

    @property
    def _components(self) -> tuple[Component, ...]:
        return (self.settings, self.readings)

    async def async_update(self) -> None:
        """Refresh settings and readings with pooled block reads."""
        await self._group.async_update()

    async def async_probe(self) -> int:
        """Return holding register 62253 ("sProductType").

        A single small read; raises :class:`modbus_connection.ModbusError` if the
        unit is unreachable. CTC publishes no magic identity value, so a
        successful read is the connectivity signal - see :data:`PRODUCT_TYPE`.
        """
        (value,) = await self._unit.read_holding_registers(PROBE_REGISTER, 1)
        return value

    async def async_read_alarms(self) -> AlarmSnapshot:
        """Read the alarm / info-text buffers (registers 65133 + 65010-65069).

        A separate stateful read, deliberately kept out of :meth:`async_update`
        so a controller that rejects the 65xxx range fails only this call.
        Raises :class:`modbus_connection.ModbusError` on a transport failure.
        """
        return await self.alarms.async_read()

    async def async_write(self, component: str, field: str, value: Any) -> None:
        """Write ``value`` to ``field`` of the named component ("control_parameters").

        Raises :class:`~ctc_ecozenith.CtcValueError` if a value is out of range,
        or :class:`modbus_connection.ModbusError` on a transport failure.
        """
        await getattr(self, component).write(field, value)

    async def async_read_raw(self) -> dict[str, dict[int, int | bool]]:
        """Return the raw register image, merged across sub-systems.

        Shape: ``{"holding": {addr: word}}``. Intended for diagnostics dumps.
        """
        merged: dict[str, dict[int, int | bool]] = {}
        for component in self._components:
            for space, values in (await component.async_read_raw()).items():
                merged.setdefault(space, {}).update(values)
        return merged
