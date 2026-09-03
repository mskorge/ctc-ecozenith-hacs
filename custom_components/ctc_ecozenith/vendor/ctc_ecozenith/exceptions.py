"""Exceptions raised by ctc-ecozenith."""

from __future__ import annotations

from modbus_connection import ModbusError

__all__ = ["CtcError", "CtcValueError"]


class CtcError(ModbusError):
    """Base class for errors specific to this library."""


class CtcValueError(CtcError, ValueError):
    """A value passed to a write fell outside the range the controller accepts.

    Subclasses :class:`ValueError` so generic callers keep working, and
    :class:`CtcError` so a caller can catch every library error in one place.
    """
