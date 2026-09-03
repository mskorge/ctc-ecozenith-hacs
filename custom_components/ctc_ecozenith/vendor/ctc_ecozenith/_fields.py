"""Small helpers layered on top of ``modbus_connection.model`` field factories."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from modbus_connection.model import NumberField, gauge

from .exceptions import CtcValueError

__all__ = ["centi", "ranged", "temperature"]


def temperature(address: int, *, stride: int = 0) -> NumberField[float]:
    """A signed 16-bit register scaled by 0.1 into degrees Celsius.

    Every temperature the CTC BMS interface exposes uses this encoding
    (``Signed = 1``, ``Factor = 0,1``).
    """
    return gauge(address, 0.1, signed=True, stride=stride, unit="°C")


def centi(
    address: int, *, unit: str | None = None, signed: bool = True, stride: int = 0
) -> NumberField[float]:
    """A 16-bit register scaled by 0.1 that is *not* a temperature.

    CTC uses ``Factor = 0,1`` for many non-temperature quantities too - pump
    output %, compressor RPS, power kW, primary flow l/min, degree-minutes.
    """
    return gauge(address, 0.1, signed=signed, stride=stride, unit=unit)


def ranged(low: float, high: float) -> Callable[[Any], Any]:
    """Build a write validator that rejects values outside ``low..high`` inclusive.

    The controller silently clamps or ignores out-of-range writes, so we refuse
    them here instead and let the caller surface a clear error.
    """

    def _validate(value: Any) -> Any:
        try:
            number = float(value)
        except (TypeError, ValueError) as err:
            raise CtcValueError(f"{value!r} is not a number") from err
        if not low <= number <= high:
            raise CtcValueError(f"{number} is outside the allowed range {low}..{high}")
        return value

    return _validate
