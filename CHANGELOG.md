# Changelog

All notable changes to this integration are documented here. Versions follow
[semantic versioning](https://semver.org/); the version in
`custom_components/ctc_ecozenith/manifest.json` matches the release tag.

## 0.1.2 - 2026-09-03

### Added

- **`switch` — Extra hot water.** Triggers a hot-water top-up via control
  parameter 1006; the coordinator re-asserts it every four minutes. Turning it
  off stops re-asserting and the controller ends the top-up within five minutes
  (there is no documented "cancel now" value for 1006).
- **`binary_sensor` — Problem.** `device_class: problem`, on whenever the
  controller reports one or more active alarms; the active `E` codes (and any
  info-text `I` codes) are listed in its attributes.
- **`sensor` — Active alarm** (diagnostic). The active alarm code(s) as
  `E<n>`, or unknown when the controller is healthy.
- Alarms are read from registers `65133` + `65010`-`65069` after each poll, as
  a separate call: that range is outside the register windows proven on the
  reference unit, so a controller that rejects it logs a warning and clears the
  alarm state instead of failing the whole update.
- Vendored `ctc_ecozenith` library bumped to `v0.1.2`.

## 0.1.1 - 2026-09-03

### Fixed

- Temperature and other analogue sensors whose CTC channel is absent,
  disconnected or faulted no longer report **999.9** (raw `9999`); they now
  report **unknown**. This is the correct representation but will look like a
  regression to anyone used to seeing the `999.9` placeholder — e.g. hot-water
  and return temperature on units without those probes fitted. A Node-RED
  "clamp `999.9` → `100`" workaround is redundant on the Home Assistant side and
  can be removed.
- Vendored `ctc_ecozenith` library bumped to `v0.1.1`.

## 0.1.0 - 2026-09-03

First tagged release.

### Entities

- `sensor` — outdoor / return / radiator / primary-flow / room / DHW
  temperatures, system status and heat-pump status enums, shunt state, charge /
  brine pump and fan output %, compressor RPS, degree minutes, heat-pump and
  immersion-heater power, DHW capacity %, and read-only panel settings
  (heating-curve slope / adjustment, radiator-pump setting, vacation days).
- `binary_sensor` — radiator pump, hot-water circulation (raw register
  thresholded `> 0`).
- `climate` — heating circuit 1 (`HEAT` / `OFF` / `AUTO`), driven through
  control parameters 1015 (zone mode) and 1010 (room setpoint).
- `water_heater` — hot water comfort mode (`economy` / `normal` / `comfort`),
  driven through control parameter 1007.
- `select` — electricity price mode, driven through control parameter 1005.

### Notes

- The `climate` / `water_heater` / `select` writes target the volatile
  1000-series "Control parameters"; the coordinator re-asserts every held
  override every four minutes so the controller does not drop it.
- Writable entities report the value they are *holding* first, falling back to
  the 61500-series read-back — the manual does not promise a 1000-series write
  propagates into that block. Verify against a real unit.
- Register `62002` scaling, the `62253` product-type probe value, and a few DHW
  registers' support on the i360 are unconfirmed. See the vendored library's
  README.
- The `ctc_ecozenith` device library is vendored under
  `custom_components/ctc_ecozenith/vendor/` (library version: `v0.1.0`).
