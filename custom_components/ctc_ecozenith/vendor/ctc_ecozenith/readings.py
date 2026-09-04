"""Live measurements from the 62000-62399 holding-register range.

Everything here is read-only. Addresses are the BMS register number verbatim
(base offset 0). Each declared range in :attr:`Readings.register_ranges` is a
strict subset of a 100-register window the reference Node-RED flow reads
successfully on the real unit, so no per-unit register scan is needed to poll
them; anything added *outside* those windows does need one first.
"""

from __future__ import annotations

from modbus_connection.model import Component, enum, integer

from ._fields import centi, temperature
from .enums import HeatPumpStatus, SgMode, ShuntState, SystemStatus

__all__ = ["Readings"]

# --- Estimated hot-water capacity ------------------------------------------
# The controller's own "DHW capacity %" (register 62279) drops out for long
# stretches on the reference unit (it stops updating while the tank is being
# charged). :attr:`Readings.dhw_capacity_estimate` reconstructs a percentage
# from the upper/lower tank temperatures and the stop temperature instead.
#
# SCALE / OFFSET / TOP_GAIN were least-squares fitted against the reference
# i360H's own 62279 readout over the periods when it *was* reporting; they are
# unit- and install-specific. Another unit may need them re-fitted - treat the
# estimate as indicative, and keep the raw 62279 sensor for cross-checking.
_CAP_EST_T_MIN = 40.0
_CAP_EST_SCALE = 0.9821701251125675
_CAP_EST_OFFSET = -11.827660197557327
_CAP_EST_TOP_GAIN = 1.1076


class Readings(Component):
    """Live sensor values. Everything here is read-only."""

    register_space = "holding"
    # Proven-safe windows (subsets of the flow's 62000/62100/62200/62300 blocks).
    register_ranges = (
        (62000, 62047),
        (62107, 62193),
        (62203, 62291),
        (62301, 62331),
    )
    max_span = 100

    # --- 62000 window -----------------------------------------------------
    outdoor_temperature = temperature(62000)
    dhw_stop_temperature = temperature(62001)
    # Manual Factor for 62002 is "1", but its neighbours 62001/62003 and the
    # matching setpoint 61502 are all Factor 0,1; the reference flow scales this
    # by 0.1 too. Treat the manual as a typo. Verify live against 61502.
    dhw_outlet_setpoint = temperature(62002)
    dhw_temperature = temperature(62003)
    system_status = enum(62005, SystemStatus)
    radiator_water_temperature = temperature(62006)
    hs1_primary_flow_setpoint = temperature(62007)
    hs1_primary_flow_temperature = temperature(62011)
    return_temperature = temperature(62015)
    # 0/1 on the reference unit; a sibling pump reg (62323) is documented 0-100,
    # so model raw and let the consumer threshold it.
    dhw_circulation = integer(62016, signed=False)
    hp1_status = enum(62017, HeatPumpStatus)
    hp1_supply_temperature = temperature(62027)  # "HP in"
    hp1_return_temperature = temperature(62037)  # "HP out"
    hp1_discharge_temperature = temperature(62047)

    # --- 62100 window ---------------------------------------------------------
    hp1_outdoor_temperature = temperature(62147)
    immersion_heater_power = centi(62168, unit="kW")
    hp1_current_rps = centi(62193, unit="rps")  # revolutions per second, not rpm
    hp1_charge_pump = centi(62107, unit="%")
    hp1_brine_pump = centi(62117, unit="%")
    hp1_fan = centi(62127, unit="%")
    degree_minutes = centi(62167)  # signed; not a duration

    # --- 62200 window ------------------------------------------------------
    hs1_room_temperature = temperature(62203)
    # Display software version, split across two registers (encoding per the
    # manual: 62244 = month/day, 62245 = year). Surfaced for diagnostics /
    # device-info; the exact packing is unverified against a real i360H.
    display_sw_version_date = integer(62244, signed=False)
    display_sw_version_year = integer(62245, signed=False)
    dhw_lower_tank_setpoint = temperature(62274)
    dhw_lower_temperature = temperature(62275)
    dhw_upper_temperature = temperature(62276)
    dhw_capacity = centi(62279, unit="%", signed=False)
    hp1_primary_flow = centi(62291, unit="L/min")

    # --- 62300 window ---------------------------------------------------------
    # 62301 SGMode: 0 = None/Normal, 1 = Block, 2 = Low price, 3 = High capacity.
    sg_mode = enum(62301, SgMode)
    # Spot electricity price, split across two registers: 62302 carries the
    # integer part (currency per MWh, region-dependent; signed) and 62303 the
    # four-decimal fractional part (0-9999, unsigned). Plain integers - 9999 is a
    # valid value here, so the 9999 sensor-fault sentinel must NOT be applied.
    # See :attr:`elspot_price` for the combined value.
    elspot_price_amount = integer(62302, signed=True)
    elspot_price_fraction = integer(62303, signed=False)
    radiator_pump = integer(62304, signed=False)  # 0/1 on the reference unit
    hs1_shunt_state = enum(62308, ShuntState)
    hp1_power = centi(62331, unit="kW", signed=False)

    @property
    def elspot_price(self) -> float | None:
        """Combined spot electricity price: ``62302 + 62303 / 10000``.

        In the controller's region currency per MWh. ``None`` until the first
        successful :meth:`~ctc_ecozenith.CtcEcoZenith.async_update`. The
        fixed-point convention (how the two words combine, especially for a
        negative price) is unverified against a real i360H - treat the number as
        indicative. Its main use is a liveness signal: a unit that is not being
        fed a spot price leaves both words at zero.
        """
        amount = self.elspot_price_amount
        fraction = self.elspot_price_fraction
        if amount is None or fraction is None:
            return None
        magnitude = abs(amount) + fraction / 10000
        return -magnitude if amount < 0 else magnitude

    @property
    def dhw_capacity_estimate(self) -> float | None:
        """Hot-water capacity %, reconstructed from the tank temperatures.

        A stand-in for register 62279 (:attr:`dhw_capacity`), which stalls for
        long periods on the reference unit while the tank is charging. Combines
        the upper (62276) and lower (62275) tank temperatures against the stop
        temperature (62001), with a temperature-spread-weighted blend of the two
        tank readings and an empirical linear correction (see the ``_CAP_EST_*``
        constants). ``None`` until those registers are populated, or when the
        stop temperature is at or below the 40 degC floor. Clamped to 0-100.
        """
        upper = self.dhw_upper_temperature
        lower = self.dhw_lower_temperature
        target = self.dhw_stop_temperature
        if upper is None or lower is None or target is None:
            return None
        span = target - _CAP_EST_T_MIN
        if span <= 0:
            return None
        spread = max(upper - lower, 0.0)
        weight = min(max(0.5 + 0.06 * spread, 0.5), 1.1)
        upper_gap = max(upper - _CAP_EST_T_MIN, 0.0)
        lower_gap = max(lower - _CAP_EST_T_MIN, 0.0)
        base = (upper_gap + weight * lower_gap) / (span * (1.0 + weight)) * 100.0
        pct = (_CAP_EST_SCALE * base + _CAP_EST_OFFSET) * _CAP_EST_TOP_GAIN
        return round(min(max(pct, 0.0), 100.0), 1)
