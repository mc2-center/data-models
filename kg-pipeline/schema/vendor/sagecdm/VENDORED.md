# Vendored: Sage Common Data Model (SCDM)

The `.yaml` files in this directory are a pinned, byte-identical copy of
`src/*.yaml` from:

- Source: https://github.com/Sage-Bionetworks/SageCommonDataModel
- Pinned commit: `210c73f18c1bbe75195e6028fc2aaf87f555fb22` (2026-09-01)
- License: Apache-2.0 (see the source repo's own `LICENSE`)

Vendored the same way `scripts/vendor/csv_to_linkml.py` is vendored from the
`csv-to-linkml` Claude Code skill - reproducible from a clean clone, no
dependency on cloning SageCommonDataModel itself. `make sagecdm-schema`
generates `schema/sagecdm.ttl` from `sage_cdm.yaml` (the umbrella schema)
here.

## Why pinned, not tracking `main`

Matches the DUO-pinned-version governance discipline already documented in
`README.md`'s "Interoperating with sagebrain-model" section: SCDM is still
Phase 1 (ORGANIZATION/PERSON/PROGRAM/PROJECT/STUDY; PORTAL and the
PERSON-role-assignment relationship are tracked as SCDM-2/not yet
implemented) and evolving independently of this repo. Silently picking up
upstream changes on every regeneration would let this pipeline's crosswalks
(`mappings/crosswalks/institution_to_scdm_organization.tsv`,
`consortium_to_scdm_program.tsv`) drift out of sync with whatever id
patterns/slot shapes SCDM actually has at generation time, with no visible
diff pointing at the cause.

## Re-vendoring

Re-vendor deliberately, not automatically:

```bash
cp /path/to/SageCommonDataModel/src/*.yaml schema/vendor/sagecdm/
```

then update the pinned commit hash above and re-run `make sagecdm-schema`.
Check `schema/vendor/sagecdm/*.yaml`'s diff against this pin before
re-generating anything downstream - a class/slot rename upstream would
silently break `scripts/link_scdm.py`'s hardcoded id patterns
(`org.<slug>`, `program.<slug>`) otherwise.
