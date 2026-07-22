# Controlled Vocabulary Description & Ontology Backfill Report

This report tracks every valid-value term whose `Description` and/or
`Ontology Identifier`/`Ontology Url`/`NCIt Code` was populated by this pass,
separate from any `*_decisions.json` worklist format used by prior OLS
annotation work. It is a running log, updated as each batch of CV files is
processed across multiple turns.

## Scope

**Explicitly excluded** (per user instruction + follow-up scoping):
- `shared/therapeuticAgent.csv` (4,475 terms — explicitly out of scope)
- Administrative/identifier lists with no real ontology equivalent:
  `grant/grant_number.csv`, `grant/grant_type.csv`,
  `institution/institution_alias.csv`, `institution/institution_name.csv`,
  `institution/institution_location_state.csv`,
  `consortium/consortium_name.csv`, `consortium/consortium_funding_agency.csv`,
  `theme/theme_name.csv`, `shared/sourceGeography.csv`,
  `shared/studyLicense.csv`, `shared/dataPermission.csv`, `shared/dataTier.csv`,
  `shared/boolean.csv`,
  `tool/tool_accessibility.csv`, `tool/tool_cost.csv`,
  `tool/tool_documentation_type.csv`, `tool/tool_download_type.csv`,
  `tool/tool_license.csv`, `tool/tool_link_type.csv`,
  `tool/tool_operating_system.csv`, `tool/tool_type.csv`,
  `tool/entity_role.csv`, `tool/entity_type.csv`,
  `person/chair_roles.csv`, `person/consent_for_portal_display.csv`,
  `person/portal_display.csv`, `person/working_group_participation.csv`,
  `project/project_type.csv`

  **Judgment call flagged for review:** `tool/tool_format.csv`,
  `tool/tool_data.csv`, `tool/tool_operation.csv`, `tool/tool_topic.csv`, and
  `tool/tool_language.csv` were kept **in scope** despite living in the same
  "tool" module as several excluded files, because they describe genuine
  bioinformatics/software concepts with real ontology coverage (EDAM
  ontology's Operation/Topic/Data/Format branches), not MC2-specific
  identifiers. Say the word if you'd rather these were excluded too.

**In scope:** 65 files, ~4,850 missing descriptions (see per-batch tables
below for the authoritative per-file list).

## Confidence rubric

- **High** — Direct OLS match: the term's label (or an unambiguous synonym)
  matches an OLS class, and its definition is used directly or lightly
  adapted.
- **Medium** — Partial/conceptual OLS match: a related or broader/narrower
  OLS class was found and its definition adapted to fit this specific term,
  or the match required some interpretive judgment.
- **Low** — No usable OLS match found; description written by inference from
  similar terms in the same list or general domain knowledge, not grounded
  in any specific ontology record.

## Log

<!-- Entries appended per batch below. Columns: File | Term | Description source | Ontology match | Confidence -->

### Batch 1a (manually processed before switching to Agent delegation)

| File | Term | Description source | Ontology match | Confidence |
|---|---|---|---|---|
| file/eventType.csv | Enrollment | OLS: NCIT "Enrollment" | NCIT:C37948 | Medium |
| imagingLevel3Segments/objectClass.csv | Spot | Inferred from imaging/spatial-omics domain usage; no OLS match found | None | Low |
| imagingLevel4/summaryStat.csv | Not Specified | Inferred, matches sibling "Not Reported"/"Not Specified" boilerplate pattern; no OLS match found | None | Low |
| individual/metStage.csv | cM0 (i+) | OLS: NCIT "cM0 (i+) TNM Finding" (exact match) | NCIT:C95956 | High |
| individual/recurrence.csv | Not Allowed to Collect | OLS: NCIT "Not Allowed To Collect" (exact match) | NCIT:C141478 | High |
| shared/treatmentOutcome.csv | No Response | OLS: NCIT "No Response to Treatment" | NCIT:C162704 | High |
| biospecimen/preservation.csv | Negative 80 Deg C | Inferred, analogous to sibling "Liquid Nitrogen" entry pattern; no OLS match found | None | Low |
| biospecimen/preservation.csv | Methacarn fixed paraffin embedded - MFPE | Inferred, analogous to sibling "Formalin fixed paraffin embedded - FFPE" entry; no OLS match found | None | Medium |
| biospecimen/specimenComp.csv | Normal distant | Inferred, directly analogous to sibling "Normal adjacent" entry's definition | None | Medium |
| biospecimen/specimenComp.csv | Tumor specimen from de novo untreated malignancy of the bladder | Inferred from the term's own wording; no OLS match found | None | Low |
| imagingChannel/abRole.csv | Primary | OLS: BAO (BioAssay Ontology) "primary antibody" (exact match) | BAO:0002643 | High |
| imagingChannel/abRole.csv | Secondary | OLS: BAO "secondary antibody" (exact match) | BAO:0002644 | High |
| publication/publication_accessibility.csv | Open Access | Inferred, standard definition; no OLS match found | None | Low |
| publication/publication_accessibility.csv | Restricted Access | Inferred, standard definition; no OLS match found | None | Low |
| shared/biologicalSex.csv | None of these describe me | Inferred, analogous to sibling "Decline to answer"/"Prefer not to answer" entries | None | Medium |
| shared/biologicalSex.csv | X | Inferred from common usage; no OLS match found | None | Low |
| shared/tumorGrade.csv | Intermediate Grade | Inferred, directly analogous to sibling "High Grade"/G1-G4 entries in same file | None | Medium |
| shared/tumorGrade.csv | Low Grade | Inferred, directly analogous to sibling entries in same file | None | Medium |
| visiumRNALevel1/spatialReads.csv | cDNA | OLS: NCIT "cDNA" (exact match) | NCIT:C324 | High |
| visiumRNALevel1/spatialReads.csv | Spatial Barcode and UMI | Inferred from standard 10x Genomics spatial sequencing terminology; no OLS match found | None | Medium |
| biospecimen/acquisitionMethod.csv | Not specified | Inferred, matches sibling boilerplate pattern; no OLS match found | None | Low |
| biospecimen/acquisitionMethod.csv | Other | Reused from sibling "Other" rows elsewhere in the model (same NCIT code already used consistently across many files) | NCIT:C17649 | High |
| biospecimen/acquisitionMethod.csv | Re-excision | OLS: NCIT "Re-Excision" (exact match) | NCIT:C48600 | High |
| biospecimen/fixative.csv | Diimidoester | OLS: NCIT "Diimidoester" (exact match) | NCIT:C185112 | High |
| biospecimen/fixative.csv | Methacarn | Inferred from known histology/chemistry domain knowledge, analogous to sibling "Carnoy's Solution" entry; no OLS match found | None | Medium |
| biospecimen/fixative.csv | Poloxamer | Inferred from known chemistry domain knowledge; no OLS match found | None | Low |
