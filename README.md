# CTC EcoZenith i360 for Home Assistant (HACS)

Custom integration for the **CTC EcoZenith i360** heat pump / heating system over
its **Building Management System (BMS)** Modbus TCP interface.

This is the community-testable HACS build. It bundles the
[`ctc-ecozenith`](https://github.com/mskorge/ctc-ecozenith) device library
(vendored under `custom_components/ctc_ecozenith/vendor/`) so no PyPI release is
required, and it opens its own Modbus connection. A leaner version is being
prepared for Home Assistant core.

## Installation

1. In HACS, add this repository as a custom repository (category: *Integration*).
2. Install **CTC EcoZenith i360** and restart Home Assistant.
3. *Settings → Devices & services → Add integration → CTC EcoZenith i360*, then
   enter the display's host/port (Modbus TCP needs a 3-port display) and the
   unit ID (default 1).

## Entities

| Platform | Entities |
| --- | --- |
| `sensor` | outdoor / return / radiator / primary-flow / room / DHW temperatures, system & heat-pump status, shunt state, charge / brine pump & fan output, compressor speed, degree minutes, power (heat pump, immersion heater), DHW capacity, plus read-only panel settings (heating-curve slope / adjustment, radiator-pump setting, vacation days) |
| `binary_sensor` | radiator pump, hot-water circulation |
| `climate` | heating circuit 1 |
| `water_heater` | hot water |
| `select` | electricity price mode |

## Control and the 5-minute keep-alive

The `climate`, `water_heater` and `select` entities drive CTC's **1000-series
"Control parameters"**. Those carry no write-cycle risk, but the controller
**drops any override that is not re-written within five minutes**. This
integration re-asserts every held override every four minutes for as long as
Home Assistant is running.

- `climate` heating-circuit `AUTO` mode **releases** the zone-mode and setpoint
  overrides and lets the heat curve decide; `HEAT` / `OFF` hold the circuit.
- `select` electricity-price mode `Auto (controller decides)` releases that
  override.
- After a Home Assistant restart, each entity re-asserts its last state (which
  can override a change you made on the CTC panel while HA was down).

The 61500-series user-settings registers are exposed **read-only** - the CTC
manual warns of a hard write-cycle limit on that range.

## Known limitations

The i360 is absent from the manual's model-support matrix (nearest documented
relative: EcoZenith i350/i350F). A few DHW sensors are disabled by default until
verified against a real unit, register `62002` scaling and the `62253` probe
value are unconfirmed - see the
[`ctc-ecozenith`](https://github.com/mskorge/ctc-ecozenith) README.

## Licence

Apache-2.0. The vendored library keeps its own `LICENSE` under
`custom_components/ctc_ecozenith/vendor/`.
