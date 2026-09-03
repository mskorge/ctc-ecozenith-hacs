"""Constants for the CTC EcoZenith i360 custom integration."""

from datetime import timedelta
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "ctc_ecozenith"

DEFAULT_PORT = 502
DEFAULT_SCAN_INTERVAL = 30

CONF_UNIT = "unit"

# The controller drops a 1000-series "Control parameter" override if it is not
# re-written within five minutes. Re-assert comfortably inside that window.
KEEPALIVE_INTERVAL = timedelta(minutes=4)

# Component name on the library device that holds the writable control parameters.
CONTROL_PARAMETERS = "control_parameters"
