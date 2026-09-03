"""Config flow for the CTC EcoZenith i360 custom integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .api import CtcApiClient, CtcApiError, build_connection
from .const import CONF_UNIT, DEFAULT_PORT, DOMAIN, LOGGER
from .vendor.ctc_ecozenith import PRODUCT_TYPE

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_UNIT_SELECTOR = vol.All(
    NumberSelector(NumberSelectorConfig(min=1, max=247, mode=NumberSelectorMode.BOX)),
    vol.Coerce(int),
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(),
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            NumberSelector(
                NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
            ),
            vol.Coerce(int),
        ),
        vol.Required(CONF_UNIT, default=1): _UNIT_SELECTOR,
    }
)


async def _check_connection(hass: HomeAssistant, data: dict[str, Any]) -> str | None:
    """Return an error key if the unit cannot be reached."""
    connection = build_connection(data[CONF_HOST], data[CONF_PORT])
    try:
        client = CtcApiClient(connection, data[CONF_UNIT])
        product_type = await client.async_probe()
        if PRODUCT_TYPE is not None and product_type != PRODUCT_TYPE:
            return "cannot_connect"
    except CtcApiError:
        LOGGER.debug("Cannot connect to the CTC EcoZenith unit", exc_info=True)
        return "cannot_connect"
    except Exception:  # noqa: BLE001
        LOGGER.exception("Unexpected error validating the CTC EcoZenith connection")
        return "unknown"
    finally:
        await connection.close()
    return None


class CtcEcoZenithConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CTC EcoZenith i360."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect the connection details and validate them."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**user_input, CONF_HOST: user_input[CONF_HOST].lower()}
            self._async_abort_entries_match(data)
            if error := await _check_connection(self.hass, data):
                errors["base"] = error
            else:
                return self.async_create_entry(title="CTC EcoZenith i360", data=data)
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )
