"""Read the CTC BMS alarm and info-text buffers.

Unlike settings and readings this is a *stateful* two-step read: register 65133
latches the current alarm / info-text counts and populates the buffers, then the
65010-65069 range holds them as ``(source-flag, code)`` register pairs. That
sequence can't be pooled into the :class:`~modbus_connection.model.ComponentGroup`,
so it lives here as a small helper instead.

Codes are stored as the numeric part only - 155 for CTC's ``E155``. Whether an
entry is an ``E`` (alarm) or ``I`` (info text) code is decided by which buffer it
came from, not by the value; rendering that prefix is left to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

__all__ = ["AlarmSnapshot", "Alarms", "CtcAlarm", "CtcInfoText"]

_COUNT_REGISTER = 65133
_BUFFER_START = 65010
_BUFFER_COUNT = 60  # 65010..65069 inclusive
_MAX_ALARMS = 25  # 65010..65059, two registers each
_MAX_INFOS = 5  # 65060..65069, two registers each
_INFO_OFFSET = 50  # 65060 - _BUFFER_START


@dataclass(frozen=True, slots=True)
class CtcAlarm:
    """One entry from the alarm buffer.

    ``code`` is the numeric part of the CTC ``E`` fault code (155 for ``E155``).
    ``heat_pump`` is the 65010-style flag: the alarm belongs to a heat pump
    (HP 1-10) rather than to the controller or a sensor.
    """

    code: int
    heat_pump: bool


@dataclass(frozen=True, slots=True)
class CtcInfoText:
    """One entry from the info-text buffer (numeric part of a CTC ``I`` code)."""

    code: int
    heat_pump: bool


@dataclass(frozen=True, slots=True)
class AlarmSnapshot:
    """The alarm and info-text buffers as of the last read."""

    alarms: tuple[CtcAlarm, ...] = ()
    infos: tuple[CtcInfoText, ...] = ()

    @property
    def has_alarm(self) -> bool:
        """Whether at least one alarm is active."""
        return bool(self.alarms)

    @property
    def alarm_count(self) -> int:
        """Number of active alarms."""
        return len(self.alarms)

    @property
    def info_count(self) -> int:
        """Number of active info texts."""
        return len(self.infos)


_EMPTY = AlarmSnapshot()


class Alarms:
    """Reads the alarm / info-text buffers off a :class:`ModbusUnit`."""

    def __init__(self, unit: ModbusUnit) -> None:
        self._unit = unit

    async def async_read(self) -> AlarmSnapshot:
        """Latch and decode the buffers.

        Reads ``65133`` (one register, which populates the buffers) on every
        call, and only reads the 60-register buffer when that count says there
        is something in it. Raises :class:`modbus_connection.ModbusError` on a
        transport failure - the caller decides whether that is fatal.
        """
        (counts,) = await self._unit.read_holding_registers(_COUNT_REGISTER, 1)
        n_alarms = min(counts & 0xFF, _MAX_ALARMS)
        n_infos = min(counts >> 8, _MAX_INFOS)
        if not n_alarms and not n_infos:
            return _EMPTY
        buf = await self._unit.read_holding_registers(_BUFFER_START, _BUFFER_COUNT)
        if len(buf) < _BUFFER_COUNT:
            return _EMPTY
        alarms = tuple(
            CtcAlarm(code=buf[i * 2 + 1], heat_pump=bool(buf[i * 2]))
            for i in range(n_alarms)
        )
        infos = tuple(
            CtcInfoText(
                code=buf[_INFO_OFFSET + i * 2 + 1],
                heat_pump=bool(buf[_INFO_OFFSET + i * 2]),
            )
            for i in range(n_infos)
        )
        return AlarmSnapshot(alarms=alarms, infos=infos)
