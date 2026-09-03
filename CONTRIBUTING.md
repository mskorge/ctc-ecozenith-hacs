# Contributing

## Development environment

Open the repository in the VS Code dev container (or run `scripts/setup` in a
Python 3.13 venv), then `scripts/develop` to start a throwaway Home Assistant
with this integration loaded.

## The vendored library

`custom_components/ctc_ecozenith/vendor/ctc_ecozenith/` is a verbatim copy of
[`ctc-ecozenith`](https://github.com/mskorge/ctc-ecozenith). **Do not edit it
here.** Change it upstream, tag a release, then re-vendor:

```
scripts/vendor /path/to/ctc-ecozenith
```

Bump `CTC_ECOZENITH_REF` in `.github/workflows/vendor-check.yml` to the new tag
and commit the updated `vendor/` tree in the same PR. CI fails if the two drift.

## Before opening a PR

1. `scripts/lint` (ruff format + check).
2. Make sure `hassfest` and `HACS` validation would pass (see
   `.github/workflows/validate.yml`).
3. Update `custom_components/ctc_ecozenith/manifest.json` `version` for a
   release (the git tag must match, with no `v` prefix).

By contributing you agree your work is licensed under the project's Apache-2.0
licence.
