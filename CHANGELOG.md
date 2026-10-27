# Changelog

All notable changes to this integration are documented here. Versions follow
[semantic versioning](https://semver.org/); the version in
`custom_components/ctc_ecozenith/manifest.json` matches the release tag.

## 0.2.2 - 2026-10-27

### Fixed

- **Hot water capacity (estimated)** no longer freezes during a 62279 dropout.
  62279 goes quiet while the tank recharges after a deep draw, and comes back
  at 99.9 % once the tank reaches its stop temperature. The estimate now
  carries on from the last value 62279 reported. It falls with the mean tank
  temperature while water is drawn (4.4 % per °C, read off three deep draws),
  then climbs in a straight line to 99.9 % at the stop temperature while the
  tank charges. It used to stay pinned at the last register value while the
  charge pump ran, or read 0 until the tank was back above about 45 °C, and it
  jumped at reconnect. The charge pump is no longer used.

## 0.2.1 - 2026-10-12

### Changed

- **Hot water capacity (estimated)** now uses the "hybrid V2" calculation. It
  reports the controller's own `Hot water capacity` (register 62279) whenever
  that has a value, and only falls back to the tank temperatures while 62279
  drops out. The temperature fallback no longer applies the extra ×1.1076 top
  gain, which overshot. While the charge pump runs, the fallback never shows
  less than the last value 62279 reported, since a tank being charged does not
  lose capacity. The entity ID and unique ID are unchanged, and the sensor is
  still disabled by default.

## 0.2.0 - 2026-10-10

### Changed

- **Requires Home Assistant 2026.9 or newer.** The integration no longer opens
  its own Modbus connection. It asks the built-in `modbus` integration for a
  unit on a shared connection (`async_get_unit`, and `async_get_temporary_unit`
  for the config-flow probe), as the
  [Modbus developer docs](https://developers.home-assistant.io/docs/modbus/introduction)
  recommend. Anything else talking to the same CTC address now shares one link
  instead of opening a competing socket. No `modbus:` YAML is needed.
- `modbus-connection` and `tmodbus` now come from Home Assistant's own `modbus`
  integration; the manifest keeps only a `modbus-connection` version floor.
- Dev tooling targets Home Assistant 2026.10.0 and Python 3.14.

### Note

- No entity, unique ID or config-entry change: upgrading needs no
  reconfiguration. The vendored `ctc_ecozenith` library is unchanged (v0.1.3).

## 0.1.4 - 2026-09-07

### Added

- **`button` — Release control.** One press drops every held 1000-series
  override at once and stops the keep-alive; it is a shortcut for setting
  `climate` to `AUTO`, `water_heater` and `select` to `auto`, and the Extra
  hot water `switch` off. It **writes nothing** to the unit — the controller
  reverts each parameter to its panel setting within five minutes. The button
  stays available even when the unit is unreachable, which is exactly when you
  want to stop the keep-alive retrying.
- Use it to tell whether Home Assistant is what keeps "[I048] Extern styrning"
  lit on the panel: press it and wait ~5 minutes. If the message clears, HA
  was the source. If it does not, the source is **outside this integration** —
  most often a bound **myUpLink** cloud connection or a wired **SG Ready**
  input at the controller's terminal block — and neither this button nor any
  entity state can clear it; disconnect that interface at the panel / wiring.
  The diagnostics download's `control_overrides` and `keepalive_active` fields
  show exactly what HA is holding.

### Note

- If "[I048] Extern styrning" persisted after 0.1.3 despite setting the
  hot-water entity to `auto`, download the diagnostics and check
  `control_overrides` / `keepalive_active` first. If `control_overrides`
  lists `hs1_room_setpoint` or `hs1_zone_mode`, the **`climate`** entity is
  the holder — dragging its target temperature once holds control parameter
  1010, which keeps the entity in `HEAT` and re-asserts on every restart;
  set **Heating circuit 1** to `AUTO` (you do not need this release for
  that). If `control_overrides` is empty and `keepalive_active` is `false`,
  Home Assistant is writing nothing and the source is outside this
  integration (myUpLink or a wired SG Ready input).

## 0.1.3 - 2026-09-04

### Changed (potentially breaking)

- **The `water_heater` (Hot water) entity's state changes for everyone on
  upgrade.** It used to mirror the panel's DHW mode (`economy` / `normal` /
  `comfort`) read back from register 61500. It now reports **`auto`** whenever
  Home Assistant is not actively forcing a mode — which, for anyone who never
  set it through HA, is always. Dashboards and automations that compare this
  entity's state or `operation_mode` attribute to `"comfort"` etc. will stop
  matching until updated. The panel's own DHW mode is still in the diagnostics
  dump and the library `settings`. This mirrors how `climate` already reports
  `AUTO` when not overridden.

### Added

- **`water_heater` — `auto` operation mode.** Selecting `auto` *releases* the
  DHW-mode override (control parameter 1007) and lets the panel setting decide,
  the same way `climate`'s `AUTO` already works. Previously every DHW selection
  was a permanent override with no way to hand control back, and a restart would
  even re-assert whatever mode the panel happened to be in — which showed on the
  panel as "[I048] Extern styrning". After upgrading, set the hot-water entity
  to `auto` to stop the re-assert.
- Electricity-price-mode `select` is now **unavailable on a unit that has never
  reported a spot electricity price** (registers `62302` / `62303` both zero).
  Control parameter `1005` only does something when the controller is fed a
  price; asserting it otherwise just lit "[I048] Extern styrning" on the panel
  for five minutes. The check latches on first sighting so the entity does not
  flap when the price lands on a whole number.
- Diagnostics dump now includes `control_overrides` (which 1000-series values
  Home Assistant is currently holding), `keepalive_active`, and an `elspot`
  block (`SGMode` 62301, the raw price words, the combined price, and whether
  the price-mode select is available) — the quickest way to see what is keeping
  "[I048] Extern styrning" lit.
- **`sensor` — Hot water capacity (estimated)** (disabled by default). A
  temperature-derived stand-in for `Hot water capacity` (register 62279), which
  stalls for long stretches while the tank is charging. Computed from the
  upper / lower tank temperatures and the stop temperature with constants
  empirically fitted to the reference unit — enable it (and, on another unit,
  expect to re-fit) only if the real 62279 sensor is unreliable for you.
- Library `readings`: `sg_mode` (register 62301 `SGMode`), `elspot_price_amount`
  / `elspot_price_fraction` (62302 / 62303) with combined `elspot_price`, and
  `dhw_capacity_estimate`.

### Changed

- Vendored `ctc_ecozenith` library bumped to `v0.1.3`.

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
