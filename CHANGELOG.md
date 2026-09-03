# Changelog

All notable changes to this integration are documented here. Versions follow
[semantic versioning](https://semver.org/); the version in
`custom_components/ctc_ecozenith/manifest.json` matches the release tag.

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
