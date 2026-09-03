# Integrate the 105-CDE CRDC required-mapping set into the MC2 model

## Context

`results/cde_match/crdc_cde_9-2-2026.csv` holds 105 Common Data Elements
extracted from the CRDC CDE Browser (`crdc_cde_9-2-2026.pdf`, cross-verified
against a caDSR `od_001` export) — the CRDC's own list of CDEs a submitting
model must map to for a required cross-DCC pipeline. This plan cross-
references that set against MC2's existing `CDE:` annotations (`Properties`
column, `modules/*/annotationProperty.csv`) and lays out how to integrate it.

**The user has reviewed every row and annotation** (in
`results/cde_match/crdc_cde_mapping_report.csv`'s `decision`/`decision_note`
columns, and inline in an earlier draft of this plan) and made the calls
below. This is now an implementation-track plan, not just a review
artifact — **no model files have been edited yet**. The four items that
were flagged as needing a further confirm (Project Name vs. Study Name,
Treatment Anatomic Site, the Specimen Anatomic Site convergence, and
ICD-10-CM Disease Code) have since been resolved by direct checks against
the module CSVs — see their sections below — so the plan is now fully
decided, not pending anything further.

**Goal framing**: the terminal objective is enabling newly-collected MC2
metadata to map cleanly onto the CRDC CDE set for the required pipeline.
That justifies renaming/realigning existing attributes and replacing their
controlled vocabularies where doing so produces a cleaner mapping (e.g.
Biospecimen Fixative → Preservation Medium terminology, several free-text
anatomic-site CVs → UBERON-coded terms) — this is **not** a purely additive,
tag-only exercise for every CDE; several of the decisions below are
deliberate breaking changes to existing attributes.

Full per-CDE detail, including every `decision`/`decision_note` and the
synthesized `recommended_action`, lives in
`results/cde_match/crdc_cde_mapping_report.csv` (one row per target CDE per
matched attribute). This document is the narrative plan; the two should be
read together and kept in sync going forward — the CSV's `decision`/
`decision_note` columns are the input record of what was decided, and
`recommended_action` is the synthesized instruction for implementation.

## Summary

| match_status | count | meaning |
|---|---|---|
| `exact_id_match` | 19 (28 attribute instances) | A `CDE:<id>` already in the model matches one of the 105 target ids exactly. |
| `new_semantic_match` | 10 | A clear best-fit MC2 attribute exists with no conflicting CDE. |
| `replace_candidate` | 6 | An MC2 attribute already carries a *different* CDE that this target CDE is a better/more-authoritative fit for. |
| `no_fit_found` | 70 | No existing attribute covered the concept at review time. |

Of the 70 `no_fit_found` CDEs, the user's decisions resolve them as:

- **25 dropped outright** — no new attribute, no mapping: the clinical
  vitals cluster (7: Body Height/Weight/BMI/BSA + units), family history
  (4), performance status (2: ECOG, Karnofsky), Race, Reported Ethnicity,
  Disease Laterality, Specimen Laterality, Specimen Longest/Shortest
  Dimension, Disease Response Criteria System, Environmental Exposure
  Type, Primary Cause of Death, Method of Diagnosis, Prior Malignancy, and
  Tumor Focality.
- **~36 confirmed as new attributes** to add (demographics minus Race/
  Ethnicity, file metadata, most specimen/treatment/diagnosis gaps, most
  UBERON-identifier companions).
- **~8 redirected onto existing attributes** as controlled-vocabulary
  replacements rather than new fields (the UBERON cluster mostly, plus
  Specimen Material Category, Project Name).

**CV consistency check — superseded by Round 8's live re-verification.**
The original pass (39 CDE/attribute pairs via the `cdeMatch` API's
name-ranking proxy) is no longer the current state — a working caDSR
`DataElement/{publicId}` endpoint was found and used in Round 8 to
re-check every flagged pair against real permissible-value data. See
Round 8 in the Implementation Report for the full resolution: most
"inconclusive" pairs are now **confirmed consistent** with real data,
two CVs were **corrected outright** (Consortium Funding Agency,
Biospecimen Preservation Medium — both had severely mismatched value
lists), two were **extended** with genuinely missing real values
(Biospecimen Composition, Treatment Response), and a few remain flagged
for a human call where the mismatch is real but the fix isn't
mechanical (Tool Entity Role's CDE looks like a poor semantic match;
Tumor Grade's real values use a different code+label serialization).
Full per-CDE detail is in `results/cde_match/crdc_cde_mapping_report.csv`'s
`cv_consistency` column, all updated in Round 8. The `GetJSON` endpoint
that was down all session is confirmed **retired**, not transient —
the working replacement (`cadsrapi.cancer.gov/rad/NCIAPI.v1_0:NciApiRad/
DataElement/{publicId}`) is now wired into
`~/.claude/skills/cadsr-cde-match/scripts/cde_match.py`'s `fetch-cde`.

## The `CRDC_CDE:` tagging decision

Add a **new, separate** `CRDC_CDE:<publicId>` token to the `Properties`
column, parallel to (not replacing) the existing `CDE:<id>` /
`CDE_version:<version>` convention, for every row below marked to add a
tag — **except** the handful of priority-fix rows (Biospecimen Tumor
Morphology, Biospecimen Site of Resection or Biopsy) where the existing
`CDE:` value is already documented as broken and should be replaced
outright rather than kept alongside a new tag.

**Why additive by default:**
- The existing `CDE:` values were curated for a different purpose and some
  were hand-fixed in a prior adversarial review ([[project-cde-match-review]]) —
  overwriting risks losing that curation history.
- The required CRDC pipeline needs a durable, greppable, unambiguous marker
  for "this attribute is one of the 105 required CRDC CDEs," independent of
  whatever generic CDE annotation the attribute already carries.
- For most `replace_candidate` rows, the existing `CDE:` value is not
  necessarily *wrong* — it's a plausible alternate CDE for a closely
  related concept (different coding scheme, different specificity).
  Conflating "add the required tag" with "fix the old mapping" would make
  the diff harder to review and revert independently — flag the old CDE
  for a separate follow-up review instead.
- For the 19 `exact_id_match` rows, the tag is numerically redundant with
  the existing `CDE:` value, but adding it anyway keeps the full 105-CDE
  required set uniformly discoverable by tag (`grep CRDC_CDE:
  modules/*/annotationProperty.csv`).

## Implementation plan

1. **Land this plan + the mapping report** as the working reference for
   the implementation PRs below. The four confirm-before-implementing flags
   from the prior draft (Project Name → Study Name overlap, the Treatment
   Anatomic Site exception, Specimen Anatomic Site's two-CDE convergence,
   ICD-10-CM's attribute-vs-new-field choice) are now resolved — see their
   sections below — based on direct checks against the module CSVs rather
   than further guesswork.

2. **Do the redundancy consolidation first** (see new section below) for
   any attribute cluster that's also getting a CV replacement in step 4 —
   e.g. consolidate Primary Diagnosis and Therapeutic Agent across
   Individual/Model/Biospecimen into one shared attribute *before*
   replacing their Valid Values with NCI-Thesaurus-coded terms, so the
   breaking CV change happens once instead of three times.

3. **Tag the confirmed exact/new/replace matches** — add `CRDC_CDE:<id>`
   to each attribute's `Properties` cell per the CSV's `recommended_action`
   column, preserving existing `CDE:`/other tags (extend the `upsert_cde()`
   pattern in `~/.claude/skills/cadsr-cde-match/scripts/cde_match.py` for a
   second tag namespace rather than replacing the first). Two rows are
   priority *replacements*, not additive tags — see "Priority fixes" below.

4. **Add the confirmed new attributes**, grouped by cluster for reviewable
   commits (see "New attributes to add" below), each with its own
   `CRDC_CDE:<id>` tag from the start. For any new enumerated attribute,
   source `Valid Values` from the CDE's real caDSR permissible-value list
   (fetch live once `GetJSON` access is restored — the bundled PDF/Excel
   extraction doesn't carry PVs) and register the new CV in
   `modules/mapping.yaml` per the existing module + collation pattern.

5. **Replace controlled vocabularies** on the attributes listed in
   "Existing attributes to re-align" below — free-text anatomic-site terms
   → UBERON-coded terms; WHO/ICD-O-based diagnosis terms and free-text
   agent names → NCI-Thesaurus-coded terms. These are breaking changes to
   existing `Valid Values`; call them out explicitly in the PR description
   and confirm downstream consumers (schematic templates, any validation
   pinned to the old CV) can absorb the change.

6. **Regenerate the model**:
   ```
   python update_valid_values.py   # any new/changed CVs registered in mapping.yaml
   make collate                    # modules/*/annotationProperty.csv -> mc2.model.csv
   make convert                    # -> mc2.model.jsonld
   make generate-json              # -> json_schemas/
   make qc
   ```
   Expect unrelated reformatting churn in any module CSV
   `update_valid_values.py` touches (pandas round-trip rewrites CSV
   quoting/line-endings, QUOTE_ALL+CRLF → QUOTE_MINIMAL+LF) —
   ([[project-cde-match-review]]) call this out in the PR description.

7. **Re-run the CV consistency check** for any new/changed enumerated
   attribute, once `GetJSON` access is restored, to confirm the newly
   adopted permissible-value lists genuinely match the CDEs they're tagged
   with (rather than just trusting the plan's assumption).

## Priority fixes (broken existing CDE refs, not additive)

Two attributes carry `CDE:` values already documented as broken
placeholders ([[project-cde-match-review]]), and both now have a confirmed
CRDC replacement:

- **Biospecimen Tumor Morphology**: `CDE:0000003` (resolves to an unrelated
  caDSR record) → replace outright with `CDE:11326261` ("ICD-O-3 Morphology
  Code"), add `CRDC_CDE:11326261`, and replace the attribute's Valid Values
  with the CDE's real ICD-O-3 permissible-value list.
- **Biospecimen Site of Resection or Biopsy**: `CDE:0000006` (resolves to
  an unrelated caDSR record) → replace outright with `CDE:14883054`
  ("Resection or Biopsy Anatomic Site UBERON Identifier"), add
  `CRDC_CDE:14883054`, and replace the attribute's Valid Values with
  UBERON-coded terms.
- **Site of Origin** (Individual/Model/Biospecimen): per user decision,
  **consolidate** these three into one shared attribute (see Redundancy
  Review below) rather than fixing Biospecimen's broken `CDE:0000004` in
  place — the consolidated attribute adopts `CDE:14156279` (Model's
  already-correct value), which fixes the broken ref as a side effect of
  the merge rather than as a standalone repair.

## New attributes to add

Grouped by cluster for reviewable commits:

- **Demographics** (4 of the original 6 — Race and Reported Ethnicity are
  dropped): Individual Year of Birth, Individual Year of Death, Individual
  Year of Diagnosis, Individual Age 90 or Older. Year of Birth/Death/
  Diagnosis carry a de-identification/PHI consideration the user has
  accepted by confirming them — no further gate.
- **File metadata** (5, all confirmed): File Data Category, File Data
  Checksum Type, File Data Checksum Value, File Data Compression Status,
  File Data Size.
- **Specimen gaps** (7, all confirmed): Biospecimen Aliquot Mass,
  Biospecimen Aliquot Volume, Biospecimen Analyte Type, the 6 Biospecimen
  "Days from `<event>` to Specimen Collection" fields (Diagnosis,
  First-Visit, First-Treatment, Initial-Genomic-Sequencing, Recurrence,
  Recurrence-to-Initial-Pathologic-Diagnosis — kept as explicit fields per
  Open Question 8 below), Biospecimen Preservation Temperature.
- **Treatment gaps** (3, all confirmed): Individual Treatment Intent Type,
  Individual Treatment or Therapy Indicator, Biospecimen Treatment Prior to
  Specimen Collection Indicator.
- **Diagnosis gaps** (all confirmed new):
  - Individual Disease Progression or Recurrence Type — confirmed new.
  - Individual Lymph Node Involvement Anatomic Site Uberon Identifier —
    confirmed new (the one UBERON-identifier CDE in this batch *not*
    redirected onto an existing attribute).
  - **ICD-10-CM Disease Code — resolved: add new companion attribute(s)**
    `Individual`/`Biospecimen ICD-10-CM Disease Code` (Enumerated by
    Reference, ICD-10-CM code pattern) alongside Primary Diagnosis, rather
    than extending Primary Diagnosis's own Valid Values. Reasoning:
    Primary Diagnosis (CDE 14905532) is already committed to an
    NCI-Thesaurus-coded CV replacement (a formal disease-*concept*
    vocabulary — see "Existing attributes to re-align" below); ICD-10-CM is
    a different, non-overlapping alphanumeric disease-*code* system (e.g.
    `C80.1`). Merging both into one Valid Values list would conflate two
    orthogonal vocabularies on a single field — CRDC/GDC itself keeps these
    as separate companion fields, and this follows the same
    companion-formal-code pattern already used for the UBERON identifiers
    and NCBI Taxonomy ID elsewhere in this plan. This overrides the
    original decision note's literal wording ("replace controlled vocab in
    existing fields"), which didn't account for the Primary Diagnosis CV
    already being spoken for by a different code system — flagging this
    reversal explicitly rather than implementing it silently.
- **Imaging** (1, confirmed): Image DICOM Modality Type.
- **Administrative** (2, confirmed): Image Platform Model Version, Project
  Short Name.
- **Project Name — resolved, corrected on review**: the original mapping
  redirected CDE 11459804 onto the *existing Study Name* attribute, which
  would have collided with Study Name's own required CDE (11459810). Direct
  check of `modules/project/annotationProperty.csv` found MC2 already has
  its own dedicated **Project Name** attribute (part of the `Project View`
  template, currently untagged) — Study and Project are distinct entities
  in this model (`Study` `DependsOn` includes a `ProjectView Key` foreign
  key). Add `CRDC_CDE:11459804` to `project`'s own Project Name attribute
  instead; Study Name keeps only `CRDC_CDE:11459810`. No coexistence
  question remains — they're simply two different attributes on two
  different entities, each with its own CDE.

## Existing attributes to re-align controlled vocabularies on

These are **breaking CV changes** (free-text terms replaced with coded
terms), not new-attribute additions — grouped because several of the
higher-value ones (Primary Diagnosis, Therapeutic Agent) also appear as
redundancy-consolidation targets below and should be re-CV'd once, on the
shared definition, not three times per entity:

- **Primary Diagnosis** (Individual/Model/Biospecimen, CDE 14905532):
  replace WHO/ICD-O-based Valid Values with NCI Thesaurus-coded terms; flag
  the current `CDE:14714127` for follow-up review once done.
- **Therapeutic Agent** (Individual/Model/Biospecimen, CDE 14913015):
  replace free-text agent-name Valid Values with the CDE's real
  NCI-Thesaurus-coded permissible-value list; flag `CDE:13579886` for
  follow-up review.
- **Biospecimen Acquisition Method** (CDE 15115495 "Specimen Procurement
  Method"): replace Valid Values with the CDE's real permissible-value
  list; flag `CDE:6626651` for follow-up review.
- **Site of Origin** (the consolidated Individual/Model/Biospecimen shared
  attribute — CDE 14883072 "Body Part Examined Anatomic Site UBERON
  Identifier", Diagnosis domain): replace the free-text disease-site Valid
  Values with UBERON-coded terms (open/reference-validated, per the
  Enumerated-by-Reference handling rule). **Resolved — no convergence after
  all**: CDE 12083894 ("Specimen Anatomic Site UBERON Identifier") looked
  like it converged on this same attribute, but its real CRDC definition is
  "the location within the body from which a specimen was *originally
  obtained*" (Specimen domain) — the physical collection site, not the
  disease site. That's a different concept, and it already has its own
  home: see Biospecimen Site of Resection or Biopsy below. The earlier
  apparent clash was a mis-assignment of 12083894, not a genuine
  one-attribute-two-CDEs case. **Note on scope**: `Biospecimen Anatomic
  Site` and `File Anatomic Site` also happen to carry `CDE:14156279` today,
  but they draw from a different curated CV source than the Site of Origin
  family (`shared/tissueOrganOriginCDS.csv`) — different contextual term
  subsets, not the same attribute, so they stay **separate attributes** and
  `CRDC_CDE:14883072` does not extend to them. **Correction (post-review)**:
  the two attributes' *own* CV sources were unified with each other (not
  with Site of Origin) — see the Implementation Report's CV-unification
  note below; this doesn't change their attribute-level separateness or the
  CRDC_CDE scoping above, only the term list they both now draw from.
- **Individual Known Metastasis Sites** (CDE 15114457 "Metastasis Anatomic
  Site UBERON Identifier"): replace free-text Valid Values with
  UBERON-coded terms. Do this after consolidating Known Metastasis Sites
  across Individual/Biospecimen (see Redundancy Review) so it happens once.
- **Biospecimen Site of Resection or Biopsy** (CDE 14883054 — see Priority
  Fixes above, **plus CDE 12083894** "Specimen Anatomic Site UBERON
  Identifier" per the resolution above): replace with UBERON-coded terms as
  part of the same commit that fixes the broken `CDE:0000006`. Both CRDC
  CDEs describe the same physical specimen-collection-site concept at
  slightly different domain granularity (Specimen vs. a more specific
  resection/biopsy procedure), so both `CRDC_CDE:` tags legitimately land on
  this one attribute — no field split needed.
- **Biospecimen Type Category** (Specimen Material Category, CDE 12445832):
  no new attribute — the existing attribute already covers the concept.
  Before tagging `CRDC_CDE:12445832` onto it, build and verify a real CV
  crosswalk between Specimen Material Category's actual caDSR permissible
  values and Biospecimen Type Category's current Valid Values; do not
  assume a 1:1 mapping without checking.

**Exception — no existing attribute to redirect onto, confirmed**:
Treatment Anatomic Site UBERON Identifier (CDE 14461856) was expected to
follow the same "replace an existing site attribute's CV" pattern as the
rest of the UBERON cluster. Direct check (grepped `modules/individual` and
`modules/model` for `site`/`anatomic`) confirms neither has any
free-text "treatment site" attribute — only Primary Site, Site of Origin,
and Known Metastasis Sites exist, all disease-related, none
treatment-related. This one genuinely needs a **new** attribute
(Individual/Model Treatment Anatomic Site, UBERON-coded from the start),
now confirmed rather than flagged.

## Resolved decisions (previously open questions)

1. **Broken placeholder refs** (`CDE:0000003`, `CDE:0000006`) — fix
   outright. See Priority Fixes above.
2. **Specimen Preservation Medium vs. Biospecimen Fixative** — same
   concept. Plan to rename/realign Biospecimen Fixative toward
   "Preservation Medium" terminology (attribute name and/or description),
   especially since Biospecimen Preservation Temperature is being added
   alongside it as a sibling field. Add `CRDC_CDE:16323957`.
3. **Specimen Material Category vs. Biospecimen Type Category** — existing
   attribute covers it; build and verify the real CV crosswalk before
   tagging (see "Existing attributes to re-align" above).
4. **Subject Age At Diagnosis (days) vs. Individual Age at Diagnosis
   (years)** — same concept, different units. Add `CRDC_CDE:10609539`
   alongside the existing `CDE:15019300`, and implement a documented
   days↔years derivation at the mapping/ETL layer (not a new stored field)
   so a CRDC submission can produce the days-based value on demand.
5. **NCBI Taxonomy ID vs. free-text Species attributes** — add a formal
   Taxonomy ID companion attribute; keep the existing free-text Species
   fields (Biospecimen/Model/File/Dataset) as-is.
6. **Person name decomposition** — confirmed: do not add decomposed
   Given/Family/Middle/prefix/suffix fields; `person` keeps a single
   combined `Name` string. **New requirement to track**: the pipeline that
   maps MC2 metadata onto these CRDC CDEs will need a name-parsing step
   (splitting the combined `Name` into components at mapping time) to
   actually populate those CDEs downstream. This is a mapping/ETL-logic
   requirement, not a model change — call it out in whatever pipeline
   documentation covers the CRDC submission process.
7. **Family history** — fully dropped. No sub-entity, no flat attributes,
   no CDE mapping for any of the 4 family-history CDEs.
8. **Specimen-collection interval fields** — keep MC2's generic Timepoint
   Offset + Timepoint Type pattern as the primary model, **and** add the 6
   explicit CRDC-named day-count fields (see "New attributes to add") so
   the required pipeline has something directly taggable; additionally,
   confirm/add Valid Values on Biospecimen Timepoint Type covering the 6
   CRDC reference events (Diagnosis, First Visit, First Treatment, Initial
   Genomic Sequencing, Recurrence, Initial Pathologic Diagnosis) so the
   generic pattern can also support downstream mapping even where the
   explicit fields aren't populated.
9. **HGNC Gene Identifier** — confirmed out of scope; MC2 doesn't model
   gene-level records.
10. **Low-confidence skip guidance** — resolved via the per-row
    `decision`/`decision_note` columns in the mapping report; no further
    mechanism needed here.

## Redundancy review: Individual / Model / Biospecimen

Separate from the CRDC integration itself: reading all three modules in
full (`modules/individual/annotationProperty.csv`,
`modules/model/annotationProperty.csv`,
`modules/biospecimen/annotationProperty.csv`) surfaces a recurring pattern
— the *same* subject-level concept (same description, same Valid Values,
and ideally the same `CDE:` tag) is independently defined once per entity
module, and in several cases the copies have already drifted: one module's
copy carries a `CDE:` tag the others are missing, or — in the clearest
case — three copies of the same concept carry three *different* CDE
states, one of them confirmed broken. This is a review only; no module CSV
has been edited.

**Recommended mechanism** (already used elsewhere in this repo, e.g. the
`<Entity> Key` foreign-key convention): define the attribute once in
`modules/shared/annotationProperty.csv`, and have each entity's component
template (`Individual`/`Model`/`Biospecimen` in their own
`annotationProperty.csv`, `IsTemplate=True` rows) list the shared attribute
name in its `DependsOn` — schematic's flat attribute namespace already
supports one attribute name being depended on by multiple components.
Each entity still gets its own per-row value; only the *definition*
(description, CV, CDE tag) stops being repeated N times.

### True duplicates (recommend consolidating)

| Attribute cluster | Modules | Current state | Recommended action |
|---|---|---|---|
| Sex | Individual, Model, Biospecimen | Identical description/CV, all `CDE:7572817` | Consolidate to one shared attribute |
| Tumor Grade | Individual, Biospecimen | Identical description/CV, both `CDE:11325685` | Consolidate |
| Last Known Disease Status | Individual, Biospecimen | Identical description/CV, **neither** currently tagged (both slated for new `CDE:12447172`) | Consolidate, then tag once |
| Treatment Type | Individual, Model, Biospecimen | Identical description/CV, all `CDE:14737565` | Consolidate |
| Treatment Response | Individual, Model, Biospecimen | Identical description/CV, all `CDE:13383448` | Consolidate |
| Therapeutic Agent | Individual, Model, Biospecimen | Identical description/CV, all `CDE:13579886` | Consolidate, then apply the NCIt-coded CV replacement (above) once |
| Primary Diagnosis | Individual, Model, Biospecimen | Identical description/CV, all `CDE:14714127` | Consolidate, then apply the NCIt-coded CV replacement (above) once |
| Primary Site | Individual, Model, Biospecimen | Identical description/CV; **only Individual** carries `CDE:14883047` | Consolidate — Model/Biospecimen inherit the correct CDE for free |
| Site of Origin | Individual, Model, Biospecimen | Same concept, same CV source (`shared/tissueOrganOriginCDS.csv` for all three in `mapping.yaml`), but three different CDE states: Individual has none, Model has `CDE:14156279`, Biospecimen has `CDE:0000004` (**confirmed broken** per prior review) | **Consolidate** into one shared attribute, adopting `CDE:14156279` (Model's correct value) — the identical CV source across all three confirms this is a true duplicate, not just a naming coincidence. Fixes the broken ref as part of the merge. |
| Known Metastasis Sites | Individual, Biospecimen | Identical description/CV, both `CDE:2856440` | Consolidate before applying the UBERON CV replacement (above) |
| Disease Type | Individual, Model, Biospecimen | Identical description/CV (Individual's description literally still reads "...associated with the specimen," a copy-paste artifact from Biospecimen); **only Individual** carries `CDE:13471160` | Consolidate |
| Tumor Subtype | Individual, Model, Biospecimen | Identical description, no CV, no CDE on any | Consolidate |
| Species | Model, Biospecimen | Identical description/CV, no CDE on either | Consolidate |
| Days to Treatment | Individual, Model | Identical description, no CDE | Consolidate |

14 clusters, 37 attribute instances collapsing to 14 shared definitions —
a net reduction of 23 attributes, each of which currently has to be kept
in sync by hand across 2–3 module files.

**Related, narrower finding — within Biospecimen itself, resolved**:
Biospecimen has *two* differently-named, differently-scoped attributes
that are easy to mistake for the same thing: **Biospecimen Anatomic Site**
(`CDE:14156279`) and **Biospecimen Site of Origin** (`CDE:0000004`,
confirmed broken, and one of the three instances folded into the Site of
Origin consolidation above). Checking `mapping.yaml` resolves the
ambiguity: Biospecimen Anatomic Site draws its CV from
`shared/anatomicSite.csv` (the same source `Individual/Biospecimen Known
Metastasis Sites` uses — a general anatomic-term catalog), not from
`shared/tissueOrganOriginCDS.csv` like the Site of Origin family. Different
curated term scope, different attribute — **Biospecimen Anatomic Site
does not participate in the Site of Origin consolidation**, and neither
does **File Anatomic Site**, despite both sharing `CDE:14156279` with that
family (coincidental, not incorrect — all ultimately describe an anatomic
location, but Site of Origin remains a separate consolidated attribute).

**Correction from the user, applied after initial implementation**: while
Biospecimen Anatomic Site and File Anatomic Site correctly stay separate
*attributes* from Site of Origin, they should **not** stay on separate CV
sources from *each other* — `shared/anatomicSite.csv` (341 terms) and
`shared/anatomicSiteImageCDS.csv` (333 terms) were merged into one
canonical `shared/anatomicSite.csv` (643 terms after dedup), and both
attributes' `mapping.yaml` entries now point to it. See the Implementation
Report for the merge/dedup mechanics — the two attributes themselves are
still independently defined and registered on their own templates.

### False positives (superficially similar, correctly kept separate)

| Attribute cluster | Why it's not a duplicate |
|---|---|
| Individual Age at Diagnosis vs. Biospecimen Age at Collection vs. Model Age | Different reference events (diagnosis vs. specimen collection vs. model use/creation) and different CDEs — genuinely distinct timepoints, not the same value duplicated. |
| Primary Site vs. Site of Origin vs. (Biospecimen) Anatomic Site | Two distinct official concepts (Primary Site → CDE 14883047 "Primary Disease Anatomic Site"; Site of Origin/Anatomic Site → CDE 14156279, a different legacy concept) that happen to sound alike in plain English. Consolidate the repetition *within* each family (see above) — don't merge the two families with each other. |
| Vital Status (Individual only) vs. Last Known Disease Status (Individual, Biospecimen) | Different concepts (alive/dead vs. detailed disease state) that happen to sit near each other conceptually; Vital Status isn't duplicated cross-module in the first place. |
| Biospecimen Timepoint Offset/Type vs. Individual/Model's specific "Days to X" fields | Different modeling approach (generic offset+label vs. one field per reference event), not a literal duplicate — this is the same design question already covered in Resolved Decision 8, not a redundancy bug. |
| Biospecimen Pathology vs. Biospecimen Tumor Status vs. Biospecimen Tumor Morphology | Three distinct concepts (pathology-report identifier vs. tumor/normal indicator vs. morphology code); Biospecimen-only, no cross-module overlap. |

## Implementation Report

Implemented directly on `cde-model-revisions` (no worktree, no commits — changes are in the
working tree for review). `schematicpy` could not be installed in this sandbox (a `PyYAML`/
Cython build failure unrelated to these changes), so `make convert` / `make qc` / `make
generate-json` were **not** run here — someone needs to run the full pipeline in a properly
configured environment before merging. `make collate` (which runs `update_valid_values.py`)
was run repeatedly during implementation and completed cleanly every time, and a manual
structural check (no new duplicate `Attribute` names, no new dangling `DependsOn` references)
passed — see below.

### Phase 1 — Priority fixes

- **Biospecimen Tumor Morphology**: `CDE:0000003` → `CDE:11326261`, added `CRDC_CDE:11326261`.
  Valid Values left untouched (plain `Enumerated`, and the existing ~700-code ICD-O-3 list
  already looks correct for this code system — no fabrication needed or attempted).
- **Biospecimen Site of Resection or Biopsy**: `CDE:0000006` → `CDE:14883054`, added
  `CRDC_CDE:14883054` and `CRDC_CDE:12083894` (the Specimen Anatomic Site convergence
  resolution). This CDE is `Enumerated by Reference`, so per the by-reference handling rule
  this attribute's ~700-term free-text anatomic-site `Valid Values` list was **cleared** and
  replaced with an open, `Pattern`-validated UBERON identifier field (`^UBERON:\d+$`),
  `Description` updated accordingly. This is a real, intentional breaking change — the old
  free-text CV is gone, not just superseded. Its stale `mapping.yaml` entry (which had been
  pointing at `shared/tissueOrganOriginCDS.csv`) was removed so `update_valid_values.py`
  won't repopulate the old list on the next collate.

### Phase 2 — Redundancy consolidation

All 14 clusters from the plan's "True duplicates" table were verified against `mapping.yaml`
(every per-module attribute in a cluster confirmed to share the exact same CV `src` file, or
to have no CV at all) and then consolidated into `modules/shared/annotationProperty.csv`
under a bare shared name, with each entity template's `DependsOn` updated and the old
per-module `mapping.yaml` entries replaced with one `shared:` entry. All 14 passed
verification cleanly — no additional Anatomic-Site-style exceptions turned up.

Net effect: 37 old attribute instances → 14 shared definitions (**-23 attributes**), matching
the plan's estimate exactly (624 → 601 after this phase, confirmed against `git show
HEAD:mc2.model.csv`).

Judgment calls made during the merge (not fully specified in the plan, documented here per the
"make the call, document it" instruction):
- **`Required` divergence** (e.g. Individual/Model required Sex, Biospecimen didn't): kept
  `Required=True` where the majority/primary entities had it (Sex, Species, Primary
  Diagnosis), `blank` otherwise. A schematic `Required` flag is a property of the attribute
  row itself, not per-consuming-template, so per-entity differentiation isn't representable
  post-consolidation — flagging this as a real (minor) capability loss from consolidation.
- **`columnType` divergence** (e.g. Biospecimen Treatment Type was `string_list`, Individual/
  Model were plain `string`): standardized to `string_list` for Treatment Type, Therapeutic
  Agent, Disease Type, and Tumor Subtype wherever at least one existing copy already used it
  — these look like an existing oversight (real-world therapeutic agents/treatment types are
  routinely multi-valued) rather than an intentional difference, and standardizing serves the
  "make attributes consistent" goal directly.
- **Description divergence**: merged into one entity-neutral description per cluster instead
  of picking one module's wording arbitrarily (e.g. Individual Disease Type's description had
  a copy-paste artifact literally reading "...associated with the specimen" — fixed as part of
  the merge, per the plan's own callout of this bug).
- Four of the fourteen consolidated attributes were also converted to open/UBERON- or
  NCI-Thesaurus-reference-validated fields as part of Phase 5 below (Therapeutic Agent,
  Primary Diagnosis, Site of Origin, Known Metastasis Sites) — their `mapping.yaml` entries
  were **not** re-added under `shared:` (no fixed CV source applies to an open reference
  field), unlike the other 10 consolidated attributes which do keep a `shared:` CV mapping.

### Phase 3 — CRDC_CDE tagging (non-consolidated attributes)

23 already-existing attributes across `study`, `tool`, `sequencingLevel1`, `individual`,
`file`, `shared`, `biospecimen`, `person`, `grant`, `imagingLevel1`, `consortium`, and
`project` were tagged with the appropriate `CRDC_CDE:<id>` per the mapping report's
`recommended_action`. `Dataset File Formats` was deliberately left untagged (File Format is
the canonical target for `CDE:11416926`, per the user's decision to avoid double-tagging), and
`Biospecimen Description` was deliberately left untagged for `CDE:14688604` (Biospecimen
Tumor Status is the canonical target — the CDE on Description looks like a pre-existing
copy-paste leftover, flagged, not touched further).

### Phase 4 — New attributes (35)

35 new attributes added across `imagingLevel1`, `study`, `project`, `individual`, `model`,
`biospecimen`, and `file`, each registered in its module's component template `DependsOn` and
tagged with its `CRDC_CDE:<id>` from creation. Every `Description` was sourced verbatim (or
lightly adapted) from the CDE's real `CRDC Definition` in
`results/cde_match/crdc_cde_9-2-2026.csv` — no invented wording.

Per the no-fabrication rule:
- **`Enumerated by Reference`** attributes (ICD-10-CM Disease Code ×2, Lymph Node Involvement/
  Progression-or-Recurrence/Treatment Anatomic Site UBERON identifiers, Biospecimen Taxonomy
  ID): built as open fields with `Valid Values` blank and a `Pattern` for the code format
  (`^UBERON:\d+$` for UBERON; a permissive ICD-10-CM pattern; `^\d+$` for the numeric NCBI
  taxon ID).
- **`Enumerated` (plain) attributes with no CRDC-supplied example list** (Residual Disease
  Status, Age 90 or Older, Disease Progression or Recurrence Type, Treatment Intent Type,
  Treatment or Therapy Indicator, Treatment Prior to Specimen Collection Indicator, Data
  Category, Data Compression Status, Analyte Type, Preservation Temperature, DICOM Modality
  Type): left `Valid Values` blank — **flagged here as needing real permissible values sourced
  later** (live `GetJSON`/caDSR access, or a domain-expert-curated list), not invented.
- **One exception**: `File Data Checksum Type` was given `Valid Values` of `SHA-1, SHA-256,
  SHA-512` — this is not fabricated; it's the CDE's own `Example` field verbatim from the
  authoritative CRDC export, not a fixed value list.
- **`Non-enumerated`** attributes (Year of Birth/Death/Diagnosis, File Data Checksum
  Value/Size, Aliquot Mass/Volume, all 6 Days-from-X-to-Specimen-Collection fields):
  `columnType=number`, no CV concerns.
- The two `Individual`/`Model Treatment Anatomic Site` attributes and the two `Individual`/
  `Biospecimen ICD-10-CM Disease Code` attributes were added as **separate, per-entity**
  attributes (not consolidated) since they're brand new — nothing to deduplicate yet, but a
  future redundancy pass should treat them the same way the 14 clusters above were handled.

### Phase 5 — CV re-alignment on existing attributes

- **Primary Diagnosis, Therapeutic Agent, Site of Origin, Known Metastasis Sites** (all now
  consolidated shared attributes): converted to open/reference-validated fields (`Enumerated
  by Reference` per CRDC) — `Valid Values` cleared, `Description` updated to name the
  reference code system (NCI Thesaurus or UBERON), `Pattern` added where applicable
  (Site of Origin, Known Metastasis Sites). This is the single largest breaking change in this
  pass: Primary Diagnosis's ~800-term WHO/ICD-O CV and Therapeutic Agent's free-text CV are
  both gone, replaced with open reference fields. `CDE:14714127` (Primary Diagnosis) and
  `CDE:13579886` (Therapeutic Agent) were kept as the primary `CDE:` tag per the plan
  ("flag for follow-up," not "remove") — both still need the follow-up review the plan calls
  for.
- **Biospecimen Acquisition Method**: tagged `CRDC_CDE:15115495`; `Valid Values` left
  untouched (plain `Enumerated`, no live PV data available) — `CDE:6626651` flagged for
  follow-up per the plan, not changed.
- **Biospecimen Type Category / Specimen Material Category**: **not tagged.** Per the plan,
  `CRDC_CDE:12445832` requires a verified CV crosswalk before tagging, and that verification
  needs live caDSR access (currently down) — left as an explicit open follow-up rather than
  guessed at.

### Phase 6 — Fixative → Preservation Medium

`Biospecimen Fixative` renamed to `Biospecimen Preservation Medium` (`Attribute` name changed,
not just `Description`), `CRDC_CDE:16323957` added, existing `CDE:0065078` and `Valid Values`
kept as-is (plain `Enumerated`). Template `DependsOn` and the `mapping.yaml` entry (still
pointing at `biospecimen/fixative.csv`, unchanged — only the attribute name that consumes it
changed) were both updated. This is a breaking rename: anything referencing the attribute
name `Biospecimen Fixative` (manifests, downstream code, prior exports) will need updating.

### Phase 7 — Remaining resolved decisions

- **Subject Age At Diagnosis vs. Individual Age at Diagnosis**: `CRDC_CDE:10609539` added
  alongside the existing `CDE:15019300`; a days↔years derivation note appended to the
  attribute's `Description` (documentation, not a new stored field or code).
- **NCBI Taxonomy ID**: implemented in Phase 4 as `Biospecimen Taxonomy ID`, a new companion
  attribute — free-text `Biospecimen`/`Model`/`File`/`Dataset Species` fields left untouched.
- **Person name decomposition**: no model change (confirmed out of scope). The pipeline that
  maps MC2 metadata onto the CRDC CDE set will need a name-parsing step at the ETL layer to
  populate the 6 dropped person-name CDEs from the combined `Name` field — this is a note for
  whoever builds that pipeline, not something this pass could implement in the model itself.
- **Specimen-collection interval fields**: implemented both halves — the 6 explicit
  `Biospecimen Days from X to Specimen Collection` fields (Phase 4) **and** populated
  `Biospecimen Timepoint Type`'s previously-empty `Valid Values` with the 6 CRDC reference
  event names (`Diagnosis, First Visit, First Treatment, Initial Genomic Sequencing,
  Recurrence, Initial Pathologic Diagnosis`) — sourced directly from the CRDC CDE Long Names
  themselves, not invented.

### Phase 2 correction — Biospecimen/File Anatomic Site CV unification (superseded, see next section)

Applied mid-implementation, per a direct correction from the user reversing the plan's
original "leave both untouched, different CV scopes" call. Neither attribute had been touched
by any earlier phase, so no undo was needed — this was a clean addition.

**What was checked first**: `shared/anatomicSite.csv` (342 rows, 341 unique terms — `Ear`
appears twice in the pre-existing file, an unrelated harmless pre-existing duplicate) vs.
`shared/anatomicSiteImageCDS.csv` (333 rows, 333 unique terms). Exact-term overlap: only 31 —
confirming the user's finding that these are not near-duplicate lists. A further check found 39
cases where an ImageCDS term matches an anatomicSite term with a `"; NOS"` suffix added (e.g.
`Penis; NOS` vs. `Penis`) — the ICD-O-3-topography-style qualifier the user flagged.

**Merge approach**: union both files by exact `Attribute` (term) match only.
- The 31 exact-string duplicates were collapsed to one row each, with `Parent` set to
  `"Anatomic Site; File Anatomic Site"` to preserve both provenance labels on one row.
- The 39 `"; NOS"`-suffix near-matches were **not** collapsed — both the suffixed and bare
  forms were kept as distinct valid entries, per the instruction not to lose ICD-O-3 topography
  precision by guessing they're redundant.
- All other rows (310 unique to anatomicSite.csv, 302 unique to anatomicSiteImageCDS.csv) kept
  as-is with their original `Parent` label intact.
- Result: 342 + 333 − 31 = 644 by naive arithmetic, but 643 actual merged rows — the
  discrepancy is exactly the pre-existing internal `Ear` duplicate in the original
  `anatomicSite.csv` (341 unique + 333 − 31 = 643), not a merge bug.
- Column structure (`Attribute, Description, Valid Values, DependsOn, Required, Properties,
  Parent, DependsOn Component, Source, Validation Rules, Nonpreferred Terms, Ontology
  Identifier, Ontology Url, NCIt Code, Notes`) preserved unchanged; only rows were added/merged.

**Files changed**: merged content written to `modules/shared/anatomicSite.csv` (342 → 643
rows); `modules/shared/anatomicSiteImageCDS.csv` deleted (`git rm`) after confirming no other
`mapping.yaml` entry or file referenced it. `modules/mapping.yaml`'s `File Anatomic Site` entry
repointed from `shared/anatomicSiteImageCDS.csv` to `shared/anatomicSite.csv`; `Biospecimen
Anatomic Site`'s entry was already pointing at `shared/anatomicSite.csv` and needed no change.

**What did not change**: both attributes remain separate rows in their own modules
(`Biospecimen Anatomic Site` in `modules/biospecimen`, `File Anatomic Site` in `modules/file`),
each still registered only on its own template's `DependsOn`. Neither was folded into the Site
of Origin consolidation, and neither received `CRDC_CDE:14883072` — this correction is scoped
to the CV they draw from, not the attributes themselves, per the correction's explicit
instructions. Re-ran `make collate` afterward: both attributes now resolve to the identical
643-term list, and the structural check (duplicate names, dangling `DependsOn`) still shows
only the same pre-existing issues as before this correction — nothing new introduced.

### Phase 2 second correction — ontology-reference conversion supersedes the CSV merge

A further instruction from the user reframed the goal explicitly: *"consolidate CVs and use
external ontology references wherever possible. the exact content of the attributes is not
important, provided they are anchored in a real ontology."* This makes the merged-CSV approach
above the wrong final answer — reconciling two term lists is exactly the problem an open
ontology-reference field sidesteps. The merge above is superseded by this section, not stacked
on top of it.

**Reverted**: `Biospecimen Anatomic Site` and `File Anatomic Site` converted to open,
UBERON-reference-validated fields (`Valid Values` blank, `Pattern` `^UBERON:\d+$`,
`Description` naming UBERON and linking
`https://www.ebi.ac.uk/ols4/ontologies/uberon`) — the same treatment already used for Site of
Origin, Known Metastasis Sites, and the Site of Resection or Biopsy priority fix. Both
`mapping.yaml` entries removed (an open reference field has no CV source file). The merged
`modules/shared/anatomicSite.csv` (643 rows) is now itself unreferenced by anything — rather
than leave a dead 643-row file that looks authoritative but isn't, **both**
`modules/shared/anatomicSite.csv` and `modules/shared/anatomicSiteImageCDS.csv` were deleted
(`git rm -f`, confirmed no remaining `mapping.yaml` or file references first). No file was left
behind as a silent second source of truth.

**Broader sweep** (per the instruction to re-scan this session's own work, scoped to what this
session touched plus its immediate CV-sharing neighbors — not the full 600+ attribute model):
- **Known Metastasis Sites**: already correctly converted to open UBERON reference in the
  original Phase 5 work — verified, no change needed.
- **Site of Origin, Primary Diagnosis, Therapeutic Agent, Biospecimen Site of Resection or
  Biopsy**: already open-reference from earlier phases — verified, no change needed.
- **All 8 new `Enumerated by Reference` attributes from Phase 4** (ICD-10-CM Disease Code ×2,
  Lymph Node Involvement/Progression-or-Recurrence/Treatment Anatomic Site UBERON identifiers,
  Biospecimen Taxonomy ID): verified already built as open/pattern fields from creation — no
  change needed.
- **Primary Site** (CDE 14883047, "Primary Disease Anatomic Site UBERON Identifier" —
  `Enumerated by Reference`, touched this session via the redundancy consolidation but its CV
  had been left as the original ~3,300-character free-text list): **converted** — same UBERON
  open-reference treatment. This was a gap in the original implementation, caught by this
  sweep, not something the user pointed at directly.
- **Biospecimen Type Category** (CDE 11253427, "Specimen Type"/"Specimen Material OBIB
  Source" — `Enumerated by Reference` against the **Ontology for Biobanking (OBIB)**, not
  UBERON; tagged `CRDC_CDE:11253427` in Phase 3 but its small 11-value closed CV had been left
  alone): **converted** to an open field with `Pattern` `^OBIB:\d+$`. Flagged in the
  `Description` itself: `Biospecimen Analyte Type`'s "applicable when Type Category = Analyte"
  conditional note now needs re-verification once real OBIB term values are available, since
  "Analyte" was a closed-list value that may not have a 1:1 OBIB term. This conversion also
  makes the separate, still-pending `Specimen Material Category` (`CDE:12445832`) crosswalk
  question largely moot — that CDE is plain `Enumerated` (not ontology-anchored), so it
  remains a distinct, separately-tracked follow-up rather than something this conversion
  resolves.
- **Deliberately not touched**: `Biospecimen Tumor Morphology` (ICD-O-3, plain `Enumerated`,
  not by-reference) and `Biospecimen Acquisition Method` (plain `Enumerated`) — neither CDE is
  ontology-anchored per CRDC's own `VD Type`, so converting them would mean inventing a
  reference scheme CRDC itself doesn't specify. Left as closed lists per the earlier
  no-fabrication rule.

Re-ran `make collate` after this pass: clean, no errors. Structural check unchanged (same 3
pre-existing duplicate names, same 1 pre-existing dangling reference, nothing new).

### Round 2 — redundancy consolidation beyond Individual/Model/Biospecimen

A follow-up redundancy review (user-supplied, pre-verified CV-source matches per cluster)
covered 8 more clusters, some inside the original CRDC scope and some pre-existing duplication
elsewhere in the model. Same mechanism as Phase 2: move the canonical definition to
`modules/shared/annotationProperty.csv` under a bare name, update every consuming template's
`DependsOn`, update `mapping.yaml`.

1. **ICD-10-CM Disease Code** (Individual + Biospecimen) → shared `ICD-10-CM Disease Code`.
   Trivial — both were already identical open-reference fields from this session's own Phase 4.
2. **Treatment Anatomic Site** (Individual + Model) → shared `Treatment Anatomic Site`. Same,
   trivial merge of two already-identical open-reference fields.
3. **Species** — widened the existing shared `Species` (from round 1's Model+Biospecimen
   merge) to also absorb `Dataset Species`, `File Species`, `DSP Dataset Species`. All four
   used identical `src: shared/dataset_species.csv`. `File Species`'s `columnType` (`string`)
   was normalized to `string_list` to match the other three — same "one outlier looks like an
   oversight" judgment call as round 1.
4. **Data Use Codes** — widened the existing shared `Data Use Codes` (`CDE:0002001`) to absorb
   `Dataset Data Use Codes`, `File Data Use Codes`, `Study Data Use Codes`. `Dataset`/`File`
   Data Use Codes had no `mapping.yaml` entry of their own (a static, always-empty stub); `Study
   Data Use Codes` did (`shared/duo.csv`) and was removed.
5. **Assay** (new) — `Dataset Assay` + `File Assay` (carries `CRDC_CDE:12373576` — preserved
   on the merged attribute) + `Publication Assay` → shared `Assay`. `columnType` normalized to
   `string_list` (`File Assay` was the lone `string` outlier).
6. **Tissue** (new) — same pattern, `Dataset`/`File`/`Publication Tissue` → shared `Tissue`.
   `Required` judgment call: 2 of 3 (Dataset, File) left it blank, only Publication required it
   — kept blank (majority rule, consistent with round 1's approach).
7. **Tumor Type** (new) — same pattern as Tissue, same `Required`-blank majority call.
8. **Consortium Name → renamed to `Consortium Affiliation`** (new) — `Grant`/`Person`/`Project
   Consortium Name` → one shared attribute. **Naming collision caught during verification**:
   `modules/consortium/annotationProperty.csv` already has its own, semantically different
   `Consortium Name` attribute (a consortium record's own display name, used by the
   `Consortium` template) — colliding with it would have silently merged two unrelated
   concepts under one schematic attribute name. Renamed the new shared attribute to
   `Consortium Affiliation` to avoid the collision; all three templates and `mapping.yaml`
   updated to match. Separately, `columnType` was normalized to `string_list` even though 2 of
   3 (Grant, Project) used plain `string` — `Grant Consortium Name`'s original description
   carried an explicit `"1...1"` (exactly-one-value) cardinality note while `Person Consortium
   Name` explicitly allowed multiple comma-separated values; consolidating to `string_list`
   favors Person's genuine multi-value need and **loosens** Grant's single-value constraint —
   flagged here as a real, intentional tradeoff, not an oversight.

**Bugs caught by the post-merge structural check** (both fixed before considering this round
done):
- **17 other templates** (`NanoString GeoMx DSP Imaging/Level 1/2/3`, `Imaging Level 1-4`,
  `Sequencing Level 1-3`, `Sequencing RNA Level 1`, `10x Visium Auxiliary Files`/`RNA Level
  2-4`) depend directly on `File Assay`/`File Species`/`File Tissue`/`File Tumor Type`/`File
  Data Use Codes` in their *own* `DependsOn` lists, independent of the `File View` template —
  consolidating only `File View`'s `DependsOn` left all 17 dangling. Found via a full
  cross-module scan (not just the templates named in the request) and fixed by replacing the
  5 old names with the new shared names everywhere they appeared.
- **`10x Visium RNA Level 1`** has the same dependency but its template row's `IsTemplate` flag
  is blank rather than `True` (a pre-existing data quirk, unrelated to this session) — missed
  by an `IsTemplate == 'True'` filtered scan, caught by a second, unfiltered scan. Fixed the
  same way.
- A `Consortium Name` string still appears once in the final model, in `modules/consortium`'s
  own `Consortium` template `DependsOn` — confirmed this is the pre-existing, legitimate,
  never-touched attribute, not a leftover dangling reference to the renamed one.

**Net effect**: 620 attributes (636 → 620, **−16**), matching the arithmetic exactly (2
trivial merges at −1 each, 2 widen-existing-target merges at −3 each, 4 new-shared merges at
−2 each = −16). Re-ran `make collate`: clean. Final structural check: same 3 pre-existing
duplicate names (`dataUseModifiers`, `license`, `Tool Grant Number`) and the same 1
pre-existing dangling reference (`Study` → `Study Number of Samples`) as every prior check in
this document — nothing new introduced by round 2.

### Round 2 addendum — `sharingPlans` gap found via `mapping.yaml` src-grouping

A follow-up check (grouping every `mapping.yaml` entry by identical `src` value, rather than by
name-prefix pattern) found `modules/sharingPlans` (`DataDSP` template) had **four** more
un-consolidated duplicates of clusters already merged above — missed the first time because
name-pattern matching doesn't reliably catch a `"DSP Dataset X"` / `"DSP X"` prefix:

- `DSP Dataset Assay` (`src: shared/assay.csv`) → folded into shared `Assay`.
- `DSP Dataset Tissue` (`src: shared/tissue.csv`) → folded into shared `Tissue`.
- `DSP Dataset Tumor Type` (`src: shared/tumorType.csv`) → folded into shared `Tumor Type`.
- `DSP Data Use Codes` — **not** caught by the `src`-grouping scan (it had no `mapping.yaml`
  entry at all, same as `Dataset`/`File Data Use Codes` before their own consolidation — the
  canonical `Data Use Codes` CV is a static hardcoded list, not `mapping.yaml`-driven). Found
  instead by directly listing every `sharingPlans` attribute and matching by name/concept
  against the already-consolidated clusters. Folded into shared `Data Use Codes`.

All four retired, `DataDSP`'s `DependsOn` updated to the shared names, the 3 `mapping.yaml`
entries removed (`DSP Data Use Codes` had none to remove).

**Full re-verification of the `src`-grouping scan**, restricted to the CV files actually used
across round 1 + round 2 (`shared/dataset_species.csv`, `shared/assay.csv`,
`shared/tissue.csv`, `shared/tumorType.csv`, `shared/duo.csv`, `consortium/consortium_name.csv`,
plus the round-1 files): every one now resolves to exactly one `shared:` entry (the by-reference
conversions correctly show zero `mapping.yaml` entries at all). The only other names still
attached to these `src` files belong to `dataCatalog` (`species`, `measurementTechnique`,
`manifestation`, `dataUseModifiers`) — a separate, deliberately schema.org/DCAT-styled module
from an earlier, unrelated integration effort, not touched by this session and out of scope
here (folding it in would mean renaming a different module's intentionally-distinct vocabulary,
not deduplicating an accidental copy).

**Noted but explicitly out of scope** (found by the same broader `src`-grouping pass, but
mapping to CV files never part of round 1 or round 2, so left untouched per the instruction to
stay scoped to clusters already worked on): `Dataset File Formats` / `File Format` /
`DSP Dataset File Formats` all share `shared/dataset_file_format.csv`; `DSP Dataset Level` /
`File Level` share `file/processLevel.csv`. Both look like genuine further consolidation
candidates for a future pass, not acted on here.

**Net effect**: 616 attributes (620 → 616, **−4**, all folds into already-existing shared
targets, no new shared rows). Re-ran `make collate`: clean. Structural check: unchanged — same
3 pre-existing duplicate names, same 1 pre-existing dangling reference, nothing new.

### Verification

- `make collate` (→ `update_valid_values.py` + concatenation) ran cleanly with no errors after
  every phase.
- Structural check on the final `mc2.model.csv`: 636 attributes (624 start − 23 consolidation
  + 35 new = 636, exact match). No *new* duplicate `Attribute` names — the 3 that exist
  (`dataUseModifiers`, `license`, `Tool Grant Number`) are pre-existing in `HEAD`, unrelated to
  this work. No *new* dangling `DependsOn` references — the 1 that exists (`Study` →
  `Study Number of Samples`) is likewise pre-existing in `HEAD`.
- Cross-checked all 105 target CDEs against the final `CRDC_CDE:` tags in the modules: **72
  tagged, 33 not tagged — and all 33 reconcile exactly** against documented decisions (25
  dropped clusters/items, 6 person-name-decomposition CDEs, 1 out-of-scope HGNC CDE, 1
  pending-crosswalk-verification CDE). No accidental gaps.
- `schematicpy` schema conversion (`make convert`/`make qc`/`make generate-json`) was **not**
  run — could not be installed in this sandbox. **Required follow-up**: run
  `python update_valid_values.py && make collate && make convert && make qc &&
  make generate-json` in a working environment before merging, and treat any schematic-level
  validation errors it surfaces as the next thing to fix.

### Follow-ups for a human

1. Run the full `make all`/`make qc` pipeline in a real environment (see above) — this pass
   could only validate structure, not schematic/JSON-LD conversion.
2. Re-verify all CV replacements once caDSR `GetJSON` access is restored: Primary Diagnosis,
   Therapeutic Agent, Site of Origin, Known Metastasis Sites, Biospecimen Site of Resection or
   Biopsy (all now open/reference fields with no embedded PV list to check), plus the several
   plain-`Enumerated` attributes left with blank `Valid Values` (listed in Phase 4).
3. Build and verify the Specimen Material Category ↔ Biospecimen Type Category CV crosswalk,
   then tag `CRDC_CDE:12445832`.
4. Follow up on the four flagged-but-not-removed legacy `CDE:` tags: `14714127` (old Primary
   Diagnosis), `13579886` (old Therapeutic Agent), `6626651` (old Acquisition Method), and
   `13383448`/`15179918` coexistence on Treatment Response.
5. The `Required`-flag and `columnType` normalizations made during consolidation (Phase 2)
   are judgment calls, not explicit plan decisions — worth a second look.
6. Downstream impact audit: the Fixative rename and the 14 consolidated attribute renames
   (e.g. `Individual Sex` → `Sex`) are breaking changes to column names that any existing
   manifests, exports, or downstream code referencing the old names will need to absorb.

## Round 3 redundancy review — full model, description-first

**Review only — no files touched this round.** Prior rounds clustered candidates by grouping
`modules/mapping.yaml` entries with an identical `src` CV file. That approach is structurally
blind to any attribute with no CV at all — free-text fields, numeric fields, and the
open/reference-validated fields this session converted several attributes to. This round
instead clusters directly off `mc2.model.csv`: attribute names with a common entity prefix
stripped (`Individual `, `Dataset `, `DSP Dataset `, `File `, etc.) to find same-bare-concept
candidates, then evaluates each candidate on four signals — **Description semantics**,
**Required**, **columnType/cardinality**, **Format/Pattern** — with `mapping.yaml` CV-source
match used only as secondary corroboration where available. 29 candidate clusters were found
and evaluated (the trivial `<Entity> Key` foreign-key cluster excluded as obviously-intentional
by design, not reviewed further).

### The two previously-flagged pairs, resolved with the cardinality-aware methodology

- **`Dataset File Formats` / `DSP Dataset File Formats` / `File Format`** — **splits into a true
  duplicate and a false positive.** `File Format` is `string` (Required, singular — one file has
  one format) while `Dataset File Formats` and `DSP Dataset File Formats` are both `string_list`
  ("multiple values permitted... list of extensions... included in the dataset") describing the
  same dataset-level aggregate concept, sourced from the identical CV
  (`shared/dataset_file_format.csv` for the `Dataset`/`File` pair — `DSP Dataset File Formats`
  itself has no separate `mapping.yaml` entry, but its description and cardinality match
  exactly). **Verdict**: `File Format` vs. the other two — **false positive**, confirms the
  user's own worked example exactly (one file : one format vs. one dataset : many files : many
  formats). `Dataset File Formats` vs. `DSP Dataset File Formats` — **true duplicate**,
  recommend consolidating those two specifically (not `File Format`).
- **`File Level` / `DSP Dataset Level`** — **false positive**, same reasoning: `File Level`
  is `string`/Required (one file, one processing level); `DSP Dataset Level` is dataset-scoped.
  Correctly separate by granularity. Side finding, not a cross-attribute duplicate: `DSP Dataset
  Level`'s own description reads as singular ("The level of processing associated with the
  dataset") but its `columnType` is `string_list` — looks like an internal copy-paste-typing
  inconsistency from a sibling multi-value field, worth a human look independent of any merge.

### New true-duplicate clusters found

| Cluster | Attributes (module) | Evidence | Recommended action |
|---|---|---|---|
| **Grant Number** | `Dataset`, `Resource` (in `education`), `Person`, `Project`, `Publication`, `DSP Dataset`, `Tool` Grant Number (7) | All `string_list`, all `Required=True`, near-identical description ("Grant number(s) associated with the X('s development)... multiple values permitted"), **all 7 share the identical CV source `grant/grant_number.csv`** | Consolidate into one shared `Grant Number`, same mechanism as `Consortium Affiliation` — this is structurally the same "many entity types tag the same external grant-number vocabulary" pattern |
| **License (partial)** | `Resource` (`education`), `Tool` License | Both `string_list`, near-identical wording ("license(s) applied/permitted... multiple values"), **both share `tool/tool_license.csv`** | Consolidate `Resource License` + `Tool License`. **`Study License` is excluded** — `string` (singular), carries its own `CDE:14902606`, sourced from a different CV (`shared/studyLicense.csv`), and its description ties it to a formal CDS-submission governance requirement — genuinely distinct, not part of this cluster |
| **"DSP Dataset X" mirrors "Dataset X"** (4 pairs) | `Dataset Name`/`DSP Dataset Name`; `Dataset Alias`/`DSP Dataset Alias`; `Dataset Url`/`DSP Dataset Url`; `Dataset Description`/`DSP Dataset Description` | Each pair: same cardinality (`string`/`string`), same real-world referent (the DSP — Data Sharing Plan — module is a pre-registration/planning-stage shadow of the eventual `Dataset` record for the *same* dataset), matching or closely-paraphrased description text. `Required` diverges per pair (DSP's copy is usually less strict, consistent with "not yet finalized") — not disqualifying, same pattern already seen and accepted for `Species`/`Assay`/`Tissue`/`Tumor Type`/`Data Use Codes` in round 2 | Same DSP→Dataset consolidation mechanism used for `Assay`/`Tissue`/`Tumor Type`/`Data Use Codes`/`File Formats` this session — recommend applying it to these 4 as well. **Systemic finding**: `sharingPlans` was built as a near-complete parallel copy of `Dataset`-level fields; a dedicated pass reconciling the *whole* `DataDSP` template against `Dataset View` (not just the pairs this review happened to check) would likely find more |
| **Referenced-dataset cross-reference** | `Resource Dataset Alias` (`education`), `Publication Dataset Alias` | Both `string_list`, both describe "list of dataset alias(es) this record references/was used with," no CV source recorded for either but identical shape and role (a citing-entity's tag-list pointing at datasets) | Plausible consolidation into one shared cross-reference attribute — flagged with **medium** confidence (no CV-source corroboration available, description match is the only signal) |
| **Workflow Type** | `Workflow Type` (`shared`, generic, reused across many file-generation templates), `Visium Workflow Type` | Near-identical concept ("the workflow used to generate/analyze the file/data"), same `columnType` (`string`); `Visium Workflow Type` is `Required=True` where the shared one is blank | `Visium Workflow Type` looks like a reinvention of the already-shared `Workflow Type` rather than a genuinely Visium-specific concept — recommend `visiumRNALevel1`'s template depend on the existing shared `Workflow Type` instead of its own copy. **Medium** confidence — the `Required` divergence could reflect a deliberate Visium-specific stricter requirement rather than an oversight |

### Ambiguous — flagged for human judgment, not resolved here

| Cluster | Attributes | Why it's ambiguous |
|---|---|---|
| **Design** | `Dataset Design`, `File Design` | Both `string`, similar concept ("overall design of the dataset"), but `File Design`'s own description hedges "of the dataset **or** file" — reads like a copy-paste from `Dataset Design` that was never fully adapted to file-level scope (the same kind of artifact that caught the `Individual Disease Type` bug in round 1), but it's equally plausible file-level design genuinely needs its own value per file. Needs a domain call, not a mechanical one. |
| **Number of Participants** | `DSP Number of Participants`, `Study Number of Participants` | Both `number`; `Study`'s carries `CDE:11555662`, `DSP`'s doesn't. Real question: is a dataset's participant count always identical to its parent study's total, or can a dataset represent a *subset* of a study's full participant population (multiple datasets per study, each drawing from different or overlapping participants)? If subsets are possible, these are **not** the same fact and merging would be wrong — this needs a domain-modeling answer this review can't supply. |
| **Investigator** | `Grant Investigator`, `Project Investigator`, `Study Investigator` | Same shape as `Grant Number` (all `string_list`, `Required=True`, near-identical wording), and the same "many entities reference the same real people" pattern — but no `mapping.yaml` CV-source corroboration is available for any of the three, so this rests on description-similarity alone. Plausible true duplicate, lower confidence than `Grant Number`. |

### False positives — checked and correctly confirmed separate

Same-generic-word-across-independent-top-level-entities was the dominant pattern — each entity
(`Grant`, `Publication`, `Tool`, `Dataset`, `Resource`, `Institution`, `Consortium`, `Project`,
`Study`, `Person`) legitimately owns its own independent value for `Abstract`, `Description`
(except the `Dataset`/`DSP Dataset` pair above), `Doi`, `Full Name`, `Title`, `Type`, and most
of `Name`/`Alias`/`Url` (except the `Dataset`/`DSP Dataset` pairs above) — these are different
real-world facts, not the same fact asked redundantly, so consolidating them would be
conflating unrelated data, not deduplicating.

A few worth calling out individually because the check briefly looked promising:
- **Language**: `Resource Language` (`Pattern: [a-z]{2}`, ISO 639-1 spoken-language code) vs.
  `Tool Language` (programming language, e.g. Python/R, no pattern) — completely different
  concepts sharing only the generic word "Language." Caught cleanly by the
  `Format`/`Pattern`-divergence check (item 4 of the methodology).
- **Pubmed Id**: `Dataset Pubmed Id` (`string_list` — a dataset can cite multiple papers) vs.
  bare `Pubmed Id` (`publication` module, `string`, `CDE:3443453` — a publication's own single
  canonical PMID) vs. `Tool Pubmed Id` (`number` — the paper describing the tool). Three
  genuinely different relationships despite the shared name. Separately: `Tool Pubmed Id`'s
  `columnType=number` looks like its own representational bug (PMIDs are conventionally
  handled as strings elsewhere in this cluster) — a data-quality note, not a redundancy finding.
- **Theme Name**: `Grant Theme Name` (`Grant`'s own cross-reference tag-list to one or more
  themes) vs. bare `Theme Name` (lives in a dedicated `theme` module — the canonical name of a
  theme record itself). Different roles (reference vs. definition), not a duplicate — but this
  is the **same naming-collision risk already learned the hard way with `Consortium Name` in
  round 2** (a cross-reference field and a definitional entity's own name field sharing a bare
  noun). Flagging so a future consolidation pass doesn't repeat that mistake here.
- **Table Id**: `Biospecimen`/`Model`/`Individual Table Id` — identical `Pattern`
  (`^syn\d{7,8}$`) and shape, but each points at a **different** target metadata table. Same
  category as the `<Entity> Key` foreign-key convention — correctly separate by design.
- **Short Name**: `Project Short Name` vs. `Study Short Name` — already established this
  session as two distinct CRDC-required concepts (mirrors the `Project Name`/`Study Name`
  resolution from earlier this session) via their own separate `CRDC_CDE:` tags.
- **`Anatomic Site`** (`Biospecimen`/`File`): already resolved earlier this session (both
  converted to open UBERON-reference fields, deliberately kept as separate attributes) — not a
  new finding, re-confirmed correct on this pass.

### Summary

29 candidate clusters evaluated. **6 true-duplicate findings** (Grant Number; License-partial;
4 Dataset/DSP-Dataset pairs counted as one systemic pattern; the cross-reference Dataset-Alias
pair; Workflow Type; plus the `Dataset File Formats`/`DSP Dataset File Formats` pair carved out
of the original File-Formats flag — 6 distinct recommendations in total, spanning roughly 20
attribute instances). **3 ambiguous** clusters flagged for a human domain call rather than a
mechanical decision. The remainder (roughly 20 clusters) confirmed as false positives —
independent per-entity metadata fields that share a generic word, not the same fact asked
redundantly — with `Language`, `Pubmed Id`, and `Theme Name` called out individually since the
cardinality/Format/Pattern check is what specifically resolved them. Nothing in this section
has been implemented; it is a review artifact only, per the request.

## Round 4 — Grant Number/License consolidation + sharingPlans revert

Implemented two confirmed clusters from the Round 3 review, then reverted `sharingPlans`/
`DataDSP` out of every consolidation it had been folded into (rounds 2 and its addendum) per a
direct user decision — `sharingPlans` stays on its own DSP-prefixed attributes going forward,
even though the shared attributes it used to draw on remain consolidated for everyone else.

### Grant Affiliation (named to avoid a collision, not "Grant Number")

Consolidated `Dataset`, `Resource` (`education`), `Person`, `Project`, `Publication`, `Tool`
Grant Number (6-way, **excluding** `DSP Dataset Grant Number` per the revert below) into one
shared attribute. **Naming collision caught immediately**, same shape as `Consortium Name` in
round 2: `modules/grant/annotationProperty.csv` already has its own `Grant Number` (a Grant
record's own canonical number, e.g. `"CA123456"`, singular `string`) — colliding with it would
have merged two unrelated concepts. Renamed the new shared attribute to **`Grant Affiliation`**.

**Bigger finding along the way**: none of the 6 source attributes were actually referenced in
their own template's `DependsOn` — confirmed against `HEAD`, this is a pre-existing bug in all
six, not something this session caused. A literal "consolidation" would have just produced a
6th orphaned attribute under a new name. Treated this as the same kind of in-flight bug fix as
the `Individual Disease Type` description artifact from round 1: appended `Grant Affiliation`
to all 6 templates' `DependsOn` rather than silently preserving the orphan. As a side effect,
this also incidentally fixed the pre-existing `Tool Grant Number` **intra-module duplicate**
(two identically-named rows in `modules/tool/annotationProperty.csv` at `HEAD`) — removing the
attribute by name removed both copies at once.

### License (Resource + Tool only, Study License untouched)

Consolidated `Resource License` (`education`) + `Tool License` into shared `License` — both
`string_list`, no CDE, identical CV source (`tool/tool_license.csv`), both properly wired into
their templates already (no orphan issue here). `Study License` confirmed excluded per the
Round 3 review: singular `string`, carries its own `CDE:14902606`, different CV
(`shared/studyLicense.csv`), tied to a formal CDS-submission governance requirement.

### sharingPlans/DataDSP revert

Restored `DSP Dataset Species`, `DSP Dataset Assay`, `DSP Dataset Tissue`,
`DSP Dataset Tumor Type`, and `DSP Data Use Codes` as their own rows in
`modules/sharingPlans/annotationProperty.csv`, `DataDSP`'s `DependsOn` pointed back at the
DSP-prefixed names, and their `mapping.yaml` entries restored under `sharingPlans:` (`Data Use
Codes` has none, matching its pre-round-2 state — it's a static hardcoded CV, not
`mapping.yaml`-driven). The shared attributes (`Species`, `Assay`, `Tissue`, `Tumor Type`,
`Data Use Codes`) remain consolidated for `Dataset`/`File`/`Publication`/etc. — this revert is
scoped to `sharingPlans` only. `DSP Dataset File Formats`, `DSP Dataset Level`, and
`DSP Dataset Grant Number` were never touched by any round (File Formats/Level were only ever
*reviewed*, never implemented; Grant Number is newly created this round with
`DSP Dataset Grant Number` deliberately excluded) — nothing to revert for those three.

Per-attribute content comparison (`HEAD` original vs. restored) — checked one at a time so nothing regressed silently:

| Restored attribute | Differs from pre-round-2 `HEAD` text? | Why |
|---|---|---|
| `DSP Dataset Species` | Yes — trivial punctuation-only, content unchanged | Restored `HEAD`'s own wording verbatim ("The species the data was collected on...") — it was already clearer for this context than the merged shared version, which had drifted toward Model/Biospecimen-centric wording during round 1 |
| `DSP Dataset Assay` | **Yes, materially** | `HEAD`'s original text ("The type of data contained in this group of files") never actually said "assay." Carried forward the clearer wording from `Dataset Assay`'s own original description ("The assay the dataset is representative of") instead — a real content improvement, not a reversion |
| `DSP Dataset Tissue` | No, same content (re-scoped to dataset-only wording) | `HEAD` and the merged shared version said the same thing; shared's was just generalized across 3 entities. Restored with the dataset-only phrasing |
| `DSP Dataset Tumor Type` | No, same content (re-scoped to dataset-only wording) | Same situation as Tissue |
| `DSP Data Use Codes` | No, identical | `HEAD`'s text and the shared version were already word-for-word the same |

**Pre-existing quirk noted, not fixed** (out of scope — restoring, not repairing unrelated
bugs): `DSP Dataset Grant Number` exists as its own row but, like the 6 attributes above, was
never referenced in `DataDSP`'s own `DependsOn` at `HEAD` either — this predates every round
this session and wasn't part of what was asked to be restored/fixed here.

### Verification

Re-ran `make collate`: clean. Final attribute count: **614** (616 → 614, net −2: −6 for the
Grant Affiliation merge accounting for `Tool Grant Number`'s pre-existing intra-module
duplicate, −1 for License, +5 for the sharingPlans restore). Structural check: **2**
pre-existing duplicate names remain (`dataUseModifiers`, `license` — both `dataCatalog`
collisions, unrelated to this session throughout) — `Tool Grant Number` has now resolved itself
off that list as described above. Same 1 pre-existing dangling reference
(`Study` → `Study Number of Samples`). Nothing new introduced.

## Round 5 — Grant Affiliation correction, Study License merge, FK-vs-descriptive-field sweep

### Correction: `Grant Affiliation` retired entirely

User-verified finding: `Grant Affiliation` (created in round 4) duplicated the existing
`GrantView Key` foreign key — `GrantView_id`'s own description says it "should be equivalent
to the grant number in CAxxxxxx format," identical to `GrantView Key`'s `Pattern: CA\d{6}`,
and all 6 templates `Grant Affiliation` was wired into already had `GrantView Key`. Removed
`Grant Affiliation` from `modules/shared`, from all 6 templates' `DependsOn` (each keeps its
pre-existing `GrantView Key`), and its `mapping.yaml` entry. `grant/grant_number.csv` itself
was **not** deleted — `DSP Dataset Grant Number` (in `sharingPlans`, untouched by any round)
still uses it. This undoes part of round 4 as a correction, not a new revert request.

### `Study License` merged into shared `License`

Reversing the round-3 exclusion. Checked the two CV files before merging (same diligence as
the Anatomic Site CV reconciliation in the phase-2 correction): `tool/tool_license.csv` (326
SPDX license identifiers) vs. `shared/studyLicense.csv` (11 terms in an underscore-style
shorthand — `CC_BY`, `Apache_2`, `GPL_3`, etc.). Only `MIT` matched verbatim; the other 10 use a
different naming convention entirely. Checked whether each of `Study License`'s 10 non-matching
terms has a real SPDX equivalent already present in `tool/tool_license.csv` — **all 10 do**
(`CC0`→`CC0-1.0`, `CC_BY`→`CC-BY-4.0`, `Apache_2`→`Apache-2.0`, `GPL_3`→`GPL-3.0`,
`BSD_3_Clause`→`BSD-3-Clause`, etc.). No CSV union was needed — `Study License`'s value space is
already a strict (differently-formatted) subset of `License`'s existing CV, unlike the genuine
term-list divergence found in the Anatomic Site case.

Mechanics: `Properties` on shared `License` gained `CDE:14902606` alongside nothing else it
already had; `Description` absorbed `Study License`'s CDS-governance context ("Studies with data
submitted to CDS are required to provide a license") as a content improvement; `columnType` was
already `string_list` (no cardinality change needed, since the cluster was created that way in
round 4). **Pre-existing orphan found, same pattern as round 4's Grant Number**: `Study License`
was never in the `Study` template's own `DependsOn`, even at `HEAD` — appended `License` rather
than silently preserving a second orphan. `shared/studyLicense.csv` was **not** deleted — the
pre-existing `dataCatalog`/`shared` lowercase `license` duplicates (unrelated, documented since
the first structural check this session) still use it.

### FK-vs-descriptive-field sweep

Investigated whether other `<Entity> Key` foreign keys in `modules/shared` are duplicated by a
descriptive/reference-list attribute elsewhere, using the same evidence bar that confirmed the
`Grant Number` case: identical underlying value format, not just a related concept.

| Candidate | Investigated | Verdict |
|---|---|---|
| `Consortium Affiliation` vs. `Consortium Key` | `Consortium_id`'s real values are `program.ccbir`, `program.csbc`, etc. (slugified-prefix format). `Consortium Affiliation`'s CV (`consortium/consortium_name.csv`) uses bare acronyms (`CCBIR`, `CSBC`). Different string representations of the same real entity, not the same value space | **Keep both** — `Consortium Key` is the machine-linking FK, `Consortium Affiliation` is a human-readable reporting tag. Not the `Grant Number` situation; no action |
| `Grant Institution Name`/`Grant Institution Alias` vs. `Institution Key` | `Institution_id`'s real values are `org.arizona-state-university`-style ROR slugs. `Grant Institution Name`'s CV uses full human names ("Arizona State University"); `Grant Institution Alias` uses short forms ("ASU"). Same pattern as Consortium — different representations | **Keep both** — same reasoning as Consortium: machine-linking ID vs. human-readable name/alias for reporting |
| `Grant`/`Project`/`Study Investigator` vs. `PersonView Key` | `PersonView_id`'s description is a generic "unique primary key... using schematic," no illustrative value shown, but structurally an opaque record ID, not a human name — `Investigator` fields hold free-text people's names | **Keep both** (lower-confidence than the other two, since `PersonView_id`'s actual value format isn't directly illustrated in its own description) — a formal person-record ID and a free-text investigator-name list are very unlikely to be the same value space, but flagging the lower confidence rather than asserting it as firmly as Consortium/Institution |

**Not exhaustively re-checked**: the remaining `<Entity> Key` attributes (`Study Key`,
`DatasetView Key`, `PublicationView Key`, `ToolView Key`, `EducationalResource Key`,
`Model Key`, `Biospecimen Key`, `Individual Key`, `FileView Key`, `DataDSP Key`, and the many
Imaging/Sequencing/Visium/NanoString `*Level Key`s) — round 3's full-model sweep already
confirmed each of these entities' `Name`/`Alias`/`Doi`/etc. attributes are the entity's **own**
identity fields, not cross-references to that entity from elsewhere, so no further "X
Affiliation"-style candidate surfaced for them during this pass. Flagging that a dedicated,
narrower check of each remaining Key specifically (rather than relying on round 3's
broader sweep) could still turn up something this pass didn't look for directly — not claiming
this list is exhaustively cleared.

### Verification

Re-ran `make collate`: clean. Final attribute count: **612** (614 → 612, net −2: `Grant
Affiliation` retired, `Study License` merged away). Structural check: same 2 pre-existing
duplicate names (`dataUseModifiers`, `license`, both `dataCatalog` collisions unrelated to this
session), same 1 pre-existing dangling reference (`Study` → `Study Number of Samples`). Nothing
new introduced.

## Round 6 — exhaustive FK/PK sweep (every remaining `<Entity> Key`)

Completed the audit started in round 5. Same method throughout: find each entity's own
`<Entity>_id` primary-key row, read its `Description` for an explicit "should be equivalent to
X" statement, then check whether some *other* attribute holding that same value space
co-occurs with the `<Entity> Key` in a live template's `DependsOn` (the exact pattern that
confirmed `Grant Affiliation`). Only implemented where both conditions hold; everything weaker
is flagged, not touched.

### Full results — every Key, no omissions

| `<Entity> Key` | PK equivalence statement | Verdict |
|---|---|---|
| `GrantView Key` | "equivalent to the grant number in CAxxxxxx format" | **Fixed** (round 5 — `Grant Affiliation` retired) |
| `Consortium Key` | none in PK itself; checked via CV-format comparison | **Flagged, kept** (round 5 — `Consortium Affiliation` uses a different value format, `program.X` vs. bare acronym) |
| `Institution Key` | none | **Flagged, kept** (round 5 — `Grant Institution Name`/`Alias` use human-readable forms, `Institution_id` uses `org.X` ROR slugs) |
| `PersonView Key` | "unique primary key... using schematic" (generic) | **Flagged, kept, low confidence** (round 5 — `Investigator` fields hold free-text names vs. an opaque record ID; no illustrative value shown for `PersonView_id` itself) |
| `DatasetView Key` | **"should be equivalent to Dataset Alias"** | **Fixed** — `Resource Dataset Alias` (`education` module) co-occurred with `DatasetView Key` in `Educational Resource`'s own `DependsOn`. Retired; `DatasetView Key` (which already carries the same value per the explicit PK statement) remains. **Also flagged, not fixed**: `Publication Dataset Alias` describes the same concept, but `Publication View`'s `DependsOn` does **not** currently include `DatasetView Key` at all — no live co-occurrence to act on; fixing this would mean first deciding whether to add `DatasetView Key` to `Publication View`, a bigger design change than a same-pattern removal |
| `FileView Key` | "should be equivalent to File Alias" | **Clean, but flagging a separate finding**: `FileView Key` itself is not referenced in **any** template's `DependsOn` across the entire model (grep confirms it appears only in its own definition in `modules/shared`) — a pre-existing, model-wide dead FK, unrelated to the descriptive-field-duplication question this sweep was checking |
| `PublicationView Key` | "should be equivalent to the PubMed Id" | **Clean for live duplicates**, but **two flagged near-misses**: `Dataset Pubmed Id` and `Tool Pubmed Id` describe the same "which publication" relationship, and both `Dataset View`/`Tool View` already carry `PublicationView Key` — but neither `Dataset Pubmed Id` nor `Tool Pubmed Id` is itself wired into its own template's `DependsOn` (both orphaned, confirmed against `HEAD`). Since neither is actually live, there's nothing currently duplicated in practice — flagged for a human to decide whether to wire them up (redundant, drop) or repurpose, rather than deleting an inactive attribute on inference alone |
| `Study Key` | none | Clean — no candidate cross-reference field found |
| `Biospecimen Key` | composite (`ModelKey-Bxxx`/`IndividualKey-Bxxx`) | Clean — synthetic composite ID, no single-field twin |
| `Individual Key` | composite (`GrantNumber-INDxxx`) | Clean — same reasoning |
| `Model Key` | composite (`GrantNumber-Mxxx`) | Clean — same reasoning |
| `ToolView Key` | none | Clean |
| `EducationalResource Key` | none | Clean |
| `ProjectView Key` | none | Clean — `Project Name`/`Project Short Name` are the entity's own identity fields (already resolved distinctly earlier this session), no cross-reference duplicate found |
| `DataDSP Key` | composite (`CAxxxxxx-DSPxxx`) | Clean — includes the grant number as a prefix but isn't equivalent to any single existing field |
| `NanoStringGeoMxAuxiliaryFiles/DSPImaging/DSPLevel1/2/3 Key` (5) | "equivalent to the file Synapse Id" | Clean — Synapse IDs are opaque system identifiers, no human-readable-name twin exists anywhere in the model |
| `NanoStringGeoMXROISegmentAnnotation Key` | none (shorter description, no Synapse Id mention) | Clean |
| `ImagingChannel Key` | none | Clean |
| `ImagingLevel1/2/3Image/3Segments/4 Key` (5) | "equivalent to the file Synapse Id" | Clean — same reasoning as the NanoStringGeoMx group |
| `SequencingLevel1/2/3 Key` (3) | "equivalent to the file Synapse Id" | Clean |
| `SequencingLevel4 Key` | n/a | **Flagged as a separate, unrelated pre-existing oddity**: this Key is defined in `modules/shared` but no `sequencingLevel4` module exists anywhere in the repo — a dead reference to a component that was never built (or was removed), not a descriptive-field duplicate |
| `SequencingRNALevel1 Key` | "equivalent to the file Synapse Id" | Clean |
| `10xVisiumRNALevel1/2/3/4 Key`, `10xVisiumAuxiliaryFiles Key` (5) | "equivalent to the file Synapse Id" | Clean |

**Summary**: 31 remaining Keys audited (plus the 2 already done in round 5 — 33 total, the full
`<Entity> Key` surface in `modules/shared`). **1 new fix** this round (`Resource Dataset
Alias`). **4 new items flagged** for a human call (`Publication Dataset Alias`, `Dataset
Pubmed Id`, `Tool Pubmed Id`, the model-wide-orphaned `FileView Key` itself,
`SequencingLevel4 Key`'s dead-module reference — 5 distinct flags in total). The remaining ~27
Keys check out clean exactly as expected going in — most are Synapse-ID-backed or synthetic
composite identifiers with no natural-language twin to collide with.

### Verification

Re-ran `make collate`: clean. Final attribute count: **611** (612 → 611, −1). Structural check:
same 2 pre-existing duplicate names (`dataUseModifiers`, `license`), same 1 pre-existing
dangling reference (`Study` → `Study Number of Samples`). Nothing new.

## Round 7 — remaining recap items, structural check now fully clean

Implements every open item from the round-6 recap the user responded to. All items below are
either implemented, confirmed as no-change, or reported as still-blocked — nothing left
unaddressed. **This is the first `make collate` this session with zero pre-existing duplicate
names and zero dangling `DependsOn` references** — both of the issues carried since the very
first structural check are now resolved (see #26 and #27 below).

### Confirmed no-action items (verified unchanged)
- **#2** (`DSP`/`Study Number of Participants`): a dataset can be a real subset of a study's
  participants — genuinely different concepts, stay separate. No change made.
- **#4** (`Dataset`/`DSP Dataset` Name/Alias/Url/Description): `sharingPlans` stays fully
  separate per the user's decision. No change — already separate from round 4's revert.
- **#5** (`Dataset File Formats`/`DSP Dataset File Formats`): same as #4. No change.
- **#7** (`Workflow Type`/`Visium Workflow Type`): both kept. No change.
- **#15**: moot — `Tool Pubmed Id` deleted per #13.
- **#16, #23**: acknowledged, no action (23 remains blocked on live OBIB data as before).

### Still blocked (reported, not retried)
- **#18/#19/#20/#21-live-verification**: caDSR `GetJSON`/`GetXML` on `/invoke/caDSR/*` confirmed
  still `401 Access Denied` after retrying with varied encoding/headers — a deliberate gateway
  access change, not transient. No further API attempts made this round; #21 (below) was
  resolved using non-live reasoning instead, as instructed.
- **#17**: the hosted `schematic.api.sagebionetworks.org` has no usable CSV→JSON-LD endpoint for
  this repo's setup (needs a publicly-hosted CSV URL, returns a pickle not JSON-LD regardless).
  Locally: adding the missing `Parent`/`DependsOn Component` columns clears the header check but
  surfaces that current `schematicpy` (25.x) no longer accepts `columnType=string_list` at all —
  used extensively in this repo, including this session's own consolidation work. Pinning the
  older, compatible `schematicpy==22.8.1` fails to build (legacy `numpy.distutils`/Fortran
  toolchain issue, persists with `--no-build-isolation` and an older pinned `numpy`). This needs
  either a real schema migration (add the 2 columns for real + migrate every `string_list`) or a
  properly isolated legacy build environment — not attempted further per instruction.

### Implemented

**#1 — `File Design` description fixed.** Dropped the "of the dataset or file" hedge; now reads
"The overall design of the file, including a batch identifier, if applicable." — a genuine
file-level statement, no cross-reference to `Dataset Design`. Both attributes kept separate, as
decided.

**#3 + #10 — `Investigator` consolidated.** `Grant`/`Project`/`Study Investigator` → one shared
`Investigator` (`modules/shared`), all three templates' `DependsOn` updated. Per #10, the merged
`Description` explicitly states both accepted forms: *"Provide either the investigator's
free-text name or a PersonView_id reference (see PersonView Key) — both forms are acceptable."*
`Pattern`/`Format` left blank on purpose (no forced form). `Required=True` and `string_list`
carried over unchanged (all three source attributes already agreed on both).

**#6 — `Resource Dataset Alias` restored.** Re-added to `modules/education` using the exact
`HEAD f840848` definition the user supplied verbatim, `Educational Resource`'s `DependsOn`
restored. No `mapping.yaml` entry (never had one). `Publication View` was **not** given
`DatasetView Key` — `Publication Dataset Alias` remains a separate open flag (round 6), not
touched this round.

**#8 — `Consortium` normalized and merged; #9 — `Institution` investigated and flagged, not
merged.**
- **Consortium**: checked `consortium/consortium_id.csv` (the actual primary-key CV, 11 rows)
  against `consortium/consortium_name.csv` (used by the now-retired `Consortium Affiliation`,
  also 11 rows) — **the canonical `program.X`-format CV already carries the bare acronym for
  every row, in its own `Notes` column** (e.g. `program.csbc` → `Notes: CSBC`). No coverage gap,
  no format rewrite needed — the "normalization" the task anticipated already existed as
  metadata on the canonical record. Retired `Consortium Affiliation` from `modules/shared` and
  from all 3 templates that had it (`Grant View`, `Person View`, `Project View` — all three
  already carried `Consortium Key` too, confirmed before removing). Deleted the now-orphaned
  `consortium/consortium_name.csv` (confirmed nothing else referenced it).
- **Institution**: checked `institution/institution_id.csv` (90 rows) against
  `institution/institution_name.csv` and `institution/institution_alias.csv` (91 rows each) by
  cross-referencing their shared `Ontology Identifier` (ROR ID) column rather than row order.
  **Found a real coverage gap**: `Indiana University - Purdue University Indianapolis` (alias
  `IUPUI`) exists in both Name and Alias CVs but has **no corresponding row in
  `institution_id.csv` at all** — not even with a blank ROR ID. `Grant View` does already have
  `Institution Key` alongside `Grant Institution Name`/`Alias` (the template-co-occurrence
  condition is met), but retiring the Name/Alias fields now would make it impossible to record a
  grant's affiliation with IUPUI at all, since the FK's own picklist has no matching entry.
  **Not implemented — flagging back rather than guessing**, per the instruction: this needs
  either adding IUPUI as a real `Institution_id` record first (requires a verified ROR ID this
  session can't look up live) or a decision to accept the gap. No files changed for Institution.

**#11 — `FileView Key` removed** from `modules/shared` (confirmed unused by any template
model-wide, verified again this round).

**#12 — `SequencingLevel4 Key` removed** from `modules/shared` (dead reference — no
`sequencingLevel4` module exists anywhere in the repo).

**#13 — `Dataset Pubmed Id` and `Tool Pubmed Id` removed** entirely (both orphaned, neither ever
referenced in its own template's `DependsOn`, both redundant with `PublicationView Key`, which
both `Dataset View` and `Tool View` already carry).

**#14 — `DSP Dataset Level` `columnType` fixed**: `string_list` → `string`, matching its own
singular description ("The level of processing associated with the dataset").

**#21 — Legacy CDE tags, judged individually (no live verification available, reasoning
documented per tag):**
- **Removed** `CDE:14714127` from `Primary Diagnosis` and `CDE:13579886` from `Therapeutic
  Agent` — both attributes' `Description` and `Valid Values` were fully rewritten during
  consolidation to the CRDC/NCI-Thesaurus open-reference concept (per `CRDC_CDE:14905532` /
  `CRDC_CDE:14913015`), so the old tags no longer describe what the field actually models —
  redundant at best, actively misleading at worst.
- **Kept** `CDE:6626651` on `Biospecimen Acquisition Method` — unlike the two above, this
  attribute's `Valid Values` were deliberately left untouched this session (plain-`Enumerated`,
  no-fabrication rule), so the old tag may still validly describe the field's real, unchanged
  content. No evidence found that it's wrong; different situation from Primary
  Diagnosis/Therapeutic Agent, not a blanket rule.
- **Kept all three tags** on `Treatment Response` (`CDE:13383448`, `CRDC_CDE:13383448`,
  `CRDC_CDE:15179918`) — the `CDE:`/`CRDC_CDE:` numeric duplication is this session's
  deliberate, repo-wide convention for *every* `exact_id_match` case, not a mistake specific to
  this attribute; `CRDC_CDE:15179918` ("Best Overall Response") is a genuinely distinct,
  more-specific concept per the plan's own earlier reasoning, not a redundant restatement of
  `13383448`.

**#22 — `Biospecimen Description`'s incorrect CDE removed.** Confirmed `Biospecimen Tumor
Status` already correctly carries `CDE:14688604, CRDC_CDE:14688604` (the real target); removed
the copy-paste `CDE:14688604` from `Biospecimen Description` entirely (now blank `Properties`).

**#26 — `dataCatalog` naming collision resolved.** Renamed `dataCatalog`'s own `dataUseModifiers`
→ `dataCatalogDataUseModifiers` and `license` → `dataCatalogLicense` (camelCase, matching the
module's own DCAT/schema.org-style naming convention), updated the `DataCatalog` template's
`DependsOn` and the `mapping.yaml` entries. `modules/shared`'s long-established governance
`dataUseModifiers`/`license` (tied into the `DUOPlus1-7` chain) were **not** touched.

**#27 — `Study Number of Samples` added**, resolving the dangling reference present since the
very first structural check this session. Description adapted from `modules/governance/
Study.model.csv`'s `studySampleNumber` line, matching the sibling `Study Number of Participants`
attribute's phrasing style: *"The number of specimens associated with systematic investigation
into a subject."* `Required=True`, `Properties=CDE:11555663`, `columnType=number`. (Caught and
fixed a self-inflicted duplicate `DependsOn` entry while implementing this — `Study`'s
`DependsOn` already listed `Study Number of Samples` once, since that unresolved reference *was*
the dangling-reference finding; appending it again without checking would have produced two
entries. De-duplicated before saving.)

### #24 — Consolidated list of `Required`/`columnType` normalization judgment calls

Every cardinality/requiredness call made across every round of consolidation this session, in
one place for review (previously scattered across individual round sections):

| Attribute | Call made | Rationale |
|---|---|---|
| `Sex` (round 2) | `Required=True` | Individual/Model required it, Biospecimen didn't — majority wins |
| `Species` (round 2) | `Required=True` | Model/Biospecimen both required it |
| `Primary Diagnosis` (round 2) | `Required=True` | Individual/Model both required it |
| `Treatment Type`, `Therapeutic Agent`, `Disease Type`, `Tumor Subtype` (round 2) | `columnType` → `string_list` | At least one existing copy already used `string_list`; the `string` copies looked like an oversight given these concepts are routinely multi-valued in practice |
| `File Species` (round 2 addendum) | `columnType` `string` → `string_list` | Sole outlier vs. Dataset/DSP Species, both already `string_list` |
| `Assay` (round 2) | `columnType` → `string_list` | `File Assay` was the lone `string` outlier vs. Dataset/Publication Assay |
| `Tissue`, `Tumor Type` (round 2) | `Required` left blank | 2 of 3 source attributes (Dataset, File) left it blank; only Publication required it — majority wins |
| `License` (round 4, later widened round 5) | `Required` left blank, `columnType=string_list` | Resource/Tool both blank/`string_list` already; `Study License` (added round 5) is singular `string` by design (different cardinality, own CDE) — not force-matched, its `Required`/`columnType` were left as `License`'s own, not `Study License`'s |
| `Consortium Affiliation` → `Grant Affiliation` (round 4, **since fully retired** — rounds 5 & 7) | `Required=True`, `columnType=string_list` | Superseded; no longer applicable now that both attributes are gone |
| `Investigator` (round 7) | `Required=True`, `columnType=string_list` | All three source attributes already agreed — no divergence to resolve |
| `DSP Dataset Level` (round 7) | `columnType` `string_list` → `string` | Corrected to match its own singular description — not a cross-attribute consolidation call, a standalone data-quality fix |

**Still open, not this session's call to make**: `Visium Workflow Type`'s `Required=True` vs.
the shared `Workflow Type`'s blank (round 3 finding, #7 — user confirmed keep both, so this
divergence stands unresolved by design, not by oversight).

### Verification

Re-ran `make collate`: clean. Final attribute count: **606** (611 → 606, net −5: `Resource
Dataset Alias` +1, `Consortium Affiliation` −1, `FileView Key` −1, `SequencingLevel4 Key` −1,
`Dataset Pubmed Id` + `Tool Pubmed Id` −2, `Investigator` consolidation −2 (3 retired, 1 added),
`Study Number of Samples` +1). **Structural check: 0 duplicate attribute names, 0 dangling
`DependsOn` references** — clean for the first time this session.

## Round 8 — live caDSR data confirmed working, re-verification with real data

A working replacement for the retired `GetJSON` endpoint was found and confirmed
(`cadsrapi.cancer.gov/rad/NCIAPI.v1_0:NciApiRad/DataElement/{publicId}`, `Accept:
application/json`), along with a bulk `DataElements/getCRDCList` call returning all 105 CRDC
CDEs with complete `Used By` text and embedded permissible values for 55 of them
(`results/cde_match/crdc_cde_live_9-3-2026.csv`, `results/cde_match/crdc_cde_permissible_values.json`
— both new files, `crdc_cde_9-2-2026.csv` kept as historical record). This let several rounds'
worth of "no live data available" judgment calls be checked against the real thing.

### A — Backfilled real Valid Values on 11 previously-blank plain-Enumerated attributes

All 11 Phase-4 attributes left blank under the no-fabrication rule had real permissible-value
data in the 55-CDE set: `Individual Residual Disease Status` (5 values), `Individual Age 90 or
Older` (2), `Individual Disease Progression or Recurrence Type` (7), `Individual Treatment
Intent Type` (7), `Individual Treatment or Therapy Indicator` (4), `File Data Category` (27),
`File Data Compression Status` (3), `Image DICOM Modality Type` (89, real DICOM 2-letter
modality codes), `Biospecimen Analyte Type` (12), `Biospecimen Preservation Temperature` (10),
`Biospecimen Treatment Prior to Specimen Collection Indicator` (4). Used the `value` field (not
`long_name`) for all 11 — every one already reads as a clean, human-usable label (including the
DICOM codes, which are the actual industry-standard 2-letter abbreviations, not something to
expand to prose).

### B — Specimen Material Category ↔ Biospecimen Type Category (long-standing #20), resolved as NOT a match

Fetched CDE `12445832`'s real 19 permissible values (`Blood`, `Ascites`, `Tissue`, etc. — plain
English category names). Compared against `Biospecimen Type Category`'s current design: an open
OBIB-identifier-reference field (`Pattern ^OBIB:\d+$`, blank `Valid Values`) for the *different*
CDE `11253427`. **These are structurally incompatible** — a curator entering `Blood` would never
match the OBIB pattern. This is a real, now-confirmed misalignment, not a crosswalk waiting to
be built: the two CDEs describe a similar concept but at fundamentally different value
representations (open ontology reference vs. small closed English-language list). **Not tagging
`CRDC_CDE:12445832`** on `Biospecimen Type Category` — doing so would be actively misleading.
Left as an open design decision (new standalone attribute, or revert the OBIB conversion) rather
than resolved unilaterally. `results/cde_match/crdc_cde_mapping_report.csv`'s `12445832` row
updated with the full finding.

### C — By-reference CV conversions re-confirmed correct, not a gap

Checked whether any of the CDEs behind this session's open/reference-validated conversions
(`Primary Diagnosis`, `Therapeutic Agent`, `Site of Origin`, `Known Metastasis Sites`, `Site of
Resection or Biopsy` [both CDEs], `Primary Site`, `Biospecimen Type Category`/OBIB, `Biospecimen
Taxonomy ID`, `ICD-10-CM Disease Code`, the 3 new UBERON-identifier attributes) have real
permissible values in the live data now that fetching is possible. **None do** — all 13 are
absent from the 55-CDE permissible-values set entirely. This is positive confirmation, not a
gap: `Enumerated by Reference` genuinely means caDSR itself doesn't enumerate a value list for
these CDEs (the value comes from an external ontology/vocabulary), so the open-field design
adopted earlier this session was correct and stays as-is.

### D — Legacy CDE tags: `13383448`/`15179918` confirmed distinct with real data

Fetched both CDEs' real definitions. `13383448` ("Disease Response"): "the pathologic and/or
clinical changes... that resulted from treatment" (per-assessment-point). `15179918` ("Best
Overall Response"): "the **best** improvement... achieved **throughout the entire course** of
the protocol treatment" (a single best/final summary). This confirms the distinct-scope
reasoning from the original (non-live) judgment call. Additionally: both CDEs share an
**identical real 14-value permissible-value list** — same vocabulary, different assessment
scope, not duplicate CDEs. `6626651` (Biospecimen Acquisition Method) was independently
confirmed real and on-topic by the user's own testing before this round started. No changes to
any of the 4 legacy-tag decisions from earlier rounds — all now verified rather than reasoned.

### E — Full CV-consistency re-check with real data

Went through every "low overlap" and "inconclusive" row from the original API-ranking-based
pass; 30 of ~31 flagged CDEs had real data available (via the 55-CDE set or targeted `fetch-cde`
calls). Outcomes:

- **Confirmed consistent, no change**: `NGS Sequencing Platform` (66/67), `Sex` (all 3 real
  values present, MC2's extra 6 are a deliberate inclusive superset), `Individual Recurrence
  Status` (7/7), `Last Known Disease Status` (11/11), `NGS Library Strategy` (37/39),
  `Primary Diagnosis`/`Therapeutic Agent`/`Primary Site`/`Biospecimen Type Category` (all
  correctly by-reference, see Part C).
- **Confirmed mismatch, fixed with real data** (CV source files edited, not just
  `annotationProperty.csv` — see note below): `Consortium Funding Agency` (was 2 values `NIH`/
  `NIH-NCI`, replaced with the real 21 full agency names), `Biospecimen Preservation Medium`
  (only 4/17 real values were present under completely different terminology — e.g. `Formalin`
  vs. real `Formalin Fixed - Buffered`/`Formalin Fixed - Unbuffered` — replaced with the real
  17-value list), `Biospecimen Composition` (8/11 present, added the 3 genuinely missing real
  values: `Prior Primary`, `Progression`, `Synchronous Primary`), `Treatment Response` (added 3
  genuinely missing real values found via the `15179918`/`13383448` shared-vocabulary check:
  `Less than Partial Response`, `Too Early`, `Not Assessed`).
- **Confirmed mismatch, flagged for a human call, not changed**: `Tool Entity Role` (CDE
  `2201713`'s real 144 values are clinical/care-team roles — "Attending Physician", "Admitting
  Physician" — sharing almost nothing with the model's 7 software-project roles; this may be a
  poor CDE match despite matching by name/score, but it's a pre-existing `exact_id_match` this
  project didn't choose, so flagged rather than unilaterally retagged). `Tumor Grade` (real
  values combine code+label as one string, e.g. `G1 Low Grade`, while the model stores `G1` and
  `Low Grade` as separate list entries — same scale, different serialization; rewriting an
  already-in-use CV needs a human call).
- **Partial match, deliberately not changed**: `Biospecimen Preservation Method` (9/14 — model's
  extra values are legitimate finer-grained variants of the CDE's broader terms, e.g.
  `Cryopreservation in Liquid Nitrogen - Live Cells` vs. real's plain `Liquid Nitrogen`) and
  `Biospecimen Acquisition Method` (6/10 — same pattern, e.g. `Core Needle Biopsy` vs. real's
  plain `Needle Biopsy`). Forcing these to match the CDE's coarser terms would lose real
  granularity, not fix anything.
- **Granularity mismatch, not a contradiction**: `File Assay` (now consolidated `Assay`) — CDE
  `12373576`'s 9 broad categories (`DNA Sequencing`, `Pathology`, `Radiology`, etc.) don't
  enumerate the same items as the model's 391-value fine-grained technique list; the 2 that do
  overlap match cleanly.
- **Data artifact, not meaningful**: `Biospecimen Tumor Morphology` — the live fetch returned
  only 1 permissible value for a CDE that should have ~1000+ ICD-O-3 codes, almost certainly an
  API pagination/truncation limit for very large PV lists rather than a real single-value
  definition. Model's existing ~1150-code CV left untouched.

**Important mechanical note**: the first attempt at these CV fixes edited `Valid Values`
directly in `modules/*/annotationProperty.csv`, which `make collate` immediately overwrote back
to the old values — these 4 attributes are `mapping.yaml`-driven, so the real fix has to go into
their actual CV **source** files (`consortium/consortium_funding_agency.csv`,
`biospecimen/fixative.csv`, `biospecimen/specimenComp.csv`, `shared/treatmentOutcome.csv`), not
the generated `annotationProperty.csv` cell. Caught by re-running `make collate` and checking the
values survived before considering this done — a reminder that any future direct-CSV-edit
approach to a CV-bearing attribute must check `mapping.yaml` first.

### Verification

Re-ran `make collate` after fixing the CV-source-file issue above: clean. Structural check: 606
attributes (no new/removed rows this round — real permissible-value backfill and CV corrections
only), 0 duplicate names, 0 dangling references — unchanged from the last check, nothing broken.
