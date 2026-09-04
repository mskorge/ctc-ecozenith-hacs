"""DataUpdateCoordinator for the CTC EcoZenith i360 custom integration.

Besides polling, the coordinator owns the *keep-alive* for the 1000-series
"Control parameters": once an entity asserts one, its value is re-written every
:data:`KEEPALIVE_INTERVAL` so the controller does not drop the override. An
entity releases an override (e.g. a ``climate`` entity switched to ``auto``,
letting the heat curve decide) and the coordinator stops re-asserting it.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AlarmSnapshot, CtcApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, KEEPALIVE_INTERVAL, LOGGER

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

    from .api import CtcApiClient
    from .data import CtcConfigEntry
    from .vendor.ctc_ecozenith import CtcEcoZenith

# An override key: (library component name, field name).
type _OverrideKey = tuple[str, str]


class CtcDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Poll the CTC unit and keep 1000-series overrides alive."""

    config_entry: CtcConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: CtcConfigEntry,
        client: CtcApiClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            always_update=True,
        )
        self._client = client
        self._overrides: dict[_OverrideKey, Any] = {}
        self._cancel_keepalive: Callable[[], None] | None = None
        self._alarms = AlarmSnapshot()
        self._elspot_seen = False
        entry.async_on_unload(self._stop_keepalive)

    @property
    def alarms(self) -> AlarmSnapshot:
        """Return the last-read alarm / info-text buffers (empty on read failure)."""
        return self._alarms

    @property
    def device(self) -> CtcEcoZenith:
        """Return the library device object (read-only access)."""
        return self._client.device

    @property
    def overrides(self) -> dict[_OverrideKey, Any]:
        """Return a copy of the control-parameter overrides currently held."""
        return dict(self._overrides)

    @property
    def keepalive_active(self) -> bool:
        """Whether the 1000-series keep-alive loop is currently running."""
        return self._cancel_keepalive is not None

    @property
    def elspot_price_available(self) -> bool:
        """Whether the unit has ever reported a live spot electricity price.

        Latched: once seen it stays ``True`` for the life of the entry, so the
        electricity-price-mode ``select`` does not flap in and out of
        availability when the price happens to land on a whole number. Control
        parameter 1005 only does anything on a unit fed a spot price; without
        the feature the ``select`` is offered as unavailable rather than writing
        an override the controller would show as "[I048] Extern styrning" and
        then drop.
        """
        return self._elspot_seen

    def held(self, component: str, field: str) -> Any | None:
        """Return the value currently held for ``component.field``, or ``None``.

        Entities prefer this over the register read-back: the manual does not
        promise a 1000-series write propagates into the 61500 settings block.
        """
        return self._overrides.get((component, field))

    async def async_write_control(self, component: str, field: str, value: Any) -> None:
        """Write a control parameter and start re-asserting it."""
        try:
            await self._client.async_write(component, field, value)
        except CtcApiError as err:
            raise UpdateFailed(str(err)) from err
        self._overrides[(component, field)] = value
        self._start_keepalive()

    async def async_release_control(self, component: str, field: str) -> None:
        """Stop re-asserting ``component.field``; the controller reverts in <5 min."""
        self._overrides.pop((component, field), None)
        if not self._overrides:
            self._stop_keepalive()

    def _start_keepalive(self) -> None:
        if self._cancel_keepalive is None:
            self._cancel_keepalive = async_track_time_interval(
                self.hass, self._async_reassert, KEEPALIVE_INTERVAL
            )

    def _stop_keepalive(self) -> None:
        if self._cancel_keepalive is not None:
            self._cancel_keepalive()
            self._cancel_keepalive = None

    async def _async_reassert(self, _now: Any) -> None:
        """Re-write every held override so the controller keeps it."""
        for (component, field), value in list(self._overrides.items()):
            try:
                await self._client.async_write(component, field, value)
            except CtcApiError as err:
                LOGGER.warning(
                    "Could not re-assert %s.%s (%s); will retry", component, field, err
                )

    async def _async_update_data(self) -> None:
        """Refresh settings and readings, then the alarm buffers separately."""
        try:
            await self._client.async_update()
        except CtcApiError as err:
            raise UpdateFailed(str(err)) from err

        readings = self._client.device.readings
        if readings.elspot_price_amount or readings.elspot_price_fraction:
            self._elspot_seen = True

        # The 65xxx alarm range is outside the register windows proven on the
        # reference unit. Keep its failure isolated: a controller that rejects it
        # must not take every sensor down with it.
        try:
            self._alarms = await self._client.async_read_alarms()
        except CtcApiError as err:
            LOGGER.warning("Alarm read failed (%s); clearing alarm state", err)
            self._alarms = AlarmSnapshot()
