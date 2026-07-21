# Adversarial Review of CDE Match Results

Reviews `results/cde_match/pass2` (the full-model run, 574 attributes) against the
caDSR API itself: for every existing `CDE:<id>` annotation, every proposed "top
match," and several runner-up candidates, the actual `longName` +
`preferredDefinition` was pulled live from `cadsrapi.cancer.gov` and checked for
real semantic/domain fit — not just name-string score. Score and PV-match ratio
alone are not reliable; several systemic false-positive patterns emerged (see
bottom).

## 0. Model-integrity bugs found (independent of this match run)

These `CDE:` values are already committed in `modules/*/annotationProperty.csv` and
resolve to caDSR records that have nothing to do with the attribute, or don't
resolve at all. These predate the matcher and should be fixed regardless of what
the API proposes as a replacement.

| Attribute | Module | Current value | Resolves to | Verdict |
|---|---|---|---|---|
| Biospecimen Site of Resection or Biopsy | biospecimen | `CDE:0000006` | caDSR #6 "Patient Last Contact Date" | **Invalid — unrelated CDE, remove/replace** |
| Biospecimen Site of Origin | biospecimen | `CDE:0000004` | *no such CDE exists* | **Invalid — nonexistent ID, remove/replace** |
| Biospecimen Tumor Morphology | biospecimen | `CDE:0000003` | caDSR #3 "Lymph Node Examined Count" | **Invalid — unrelated CDE, remove/replace** |
| Data Use Codes / Study Data Use Codes / File Data Use Codes | shared/study/file | `CDE:0002001` | *no such CDE exists* | **Invalid — nonexistent ID** |
| dataUseModifiers | shared | `CDE:00002002` | caDSR #2002 "Correlative Study Findings" (retired) | **Invalid — coincidental collision, not a real match** |
| Biospecimen Incidence Type | biospecimen | `CDE:0002002` | caDSR #2002 "Correlative Study Findings" (retired) | **Invalid — same coincidental collision** |
| Study Description | study | `CDE:03444002` | caDSR #3444002 "Study Research Identification Text" | Valid concept, but this version's `registrationStatus` is `Superseded` — check for the current version |

The zero-padded 7-digit values (`0000003`, `0000004`, `0000006`, `0002001`,
`00002002`) look like placeholder/internal sequence numbers (possibly copy-pasted
from Data Use Ontology-style codes used elsewhere in the model) rather than
verified caDSR public IDs — they were never real curation decisions to begin with.

## 1. The 29 disagreements — resolved

Checked existing vs. proposed CDE by fetching both records' real definitions.

**Keep existing (27) — the API's "top match" is a false positive:**

| Attribute | Existing CDE (kept) | Why the top match is wrong |
|---|---|---|
| Biospecimen Type Category | 11253427 Specimen Material OBIB Source | Top match "Category" (6813527) is a content-free generic CDISC term |
| Biospecimen Sex | 7572817 Person Sex at Birth Category | Top match is "Body Fluid or Substance Specimen Collection Type" — matched only on the word "specimen" |
| Biospecimen Tumor Grade | 11325685 Subject Tumor Grade | Top match is a yes/no cancer-history indicator, not a grade scale |
| Biospecimen Composition | 12922545 Tumor Classification Category | Top match is "Neoadjuvant Radiation Therapy Type" — unrelated treatment CDE |
| Biospecimen Tumor Status | 14688604 Specimen Source Location Category (normal/tumor/margin) | Top match is a bone-survey-specific indicator |
| Biospecimen Preservation Method | 8028962 Specimen Preservation Procedure Type — exact fit | Top match is generic "Assessment Method Type" |
| Biospecimen Anatomic Site | 14156279 Disease Anatomic Site ICD-O-3 Site Label Text | Top match "Disease Site" is more generic/less standards-anchored |
| Biospecimen Embedding Medium | 8037927 Biospecimen Collection Medium Type | Top match "Specimen Collection Period Type" is about **time period**, not substance |
| Biospecimen / Individual / Model Primary Diagnosis | 14714127 Diagnosis Disease Text (CCDI) | Top match "Diagnosis" (7058670) is a bare generic term |
| Individual Primary Site | 14883047 Disease Primary Site Uberon Identifier — exact fit | Top match is generic "Diagnosis" |
| Biospecimen / Individual / Model Treatment Type | 14737565 Therapeutic Procedure Performed Type | Top match "Treatment Assignment Type" is about trial-arm randomization, not therapy performed |
| File Anatomic Site | 14156279 (same as above) | Top match "Infectious Disorder ... Site Name" — wrong domain (infectious disease, not oncology) |
| Individual Disease Type | 13471160 Diagnosis Disease Morphology Category | Top match is an unrelated radiation-therapy CDE |
| Individual / Model Therapeutic Agent | 13579886 Therapeutic Procedure Agent Name — exact fit | Top matches are "Non-protocol Therapy Administered Type" / "Interruption Or Modification Agent Name" — narrower/different concepts |
| Individual Metastasis Stage | 3440331 AJCC Clinical Distant Metastasis M Stage — exact fit | Top match is a binary "first distant diagnosis" indicator, not a stage |
| Individual Recurrence Status | 13529783 Disease Progression or Recurrence Indicator | Top match is a liver-toxicity CDE — matched on "indicator" only |
| Individual Treatment Response | 13383448 Disease Response Assessment Outcome (same CDE correctly used for Biospecimen/Model Treatment Response) | Top match is a **retired** adverse-event CDE |
| Model Sex | 7572817 (same as Biospecimen/Individual Sex) | Same wrong top match as above |
| NGS Library Strategy | 6273393 Molecular Analysis Library Sequencing Technique Type — exact fit | Top match "Assay Type" is broader/less specific |
| NGS Library Layout | 11527735 Molecular Analysis Sequencing Library Read Layout Type — exact fit | Top match "Medical History Event Reported Term" — wrong clinical domain |
| NGS Sequencing Platform | 6352164 Equipment Sequencing Model Name | Top match "Sequencing Library Platform Name" is a close synonym, not clearly better — keep existing |

**Replace (1) — existing is broken, and a better option exists than either side offered:**

| Attribute | Existing (reject) | API top match (also reject) | Recommended instead |
|---|---|---|---|
| Biospecimen Incidence Type | `0002002` → retired "Correlative Study Findings" (placeholder, see §0) | 7385445 "Disease Status" (0% PV overlap with Primary/Progression/Recurrence/Metastasis/Remission/No Disease) | **62997 v6 "Disease Status Type"** — 50% PV overlap and a direct definition match ("the current status of the patient's disease"), found by re-ranking this attribute's own candidate list by PV-match ratio instead of score |

**Misfiled annotation (1) — a real CDE that's on the wrong attribute:**

`Individual Last Known Disease Status` currently carries `CDE:2847330`
("Participant Vital Status Type" — literally about survival status, not
tumor/disease status). Meanwhile `Individual Vital Status` has **no** CDE, and
the matcher's own candidate list for it ranks CDE 2847330 as a runner-up with a
**perfect 5/5 permissible-value match** (better than its own top pick, "Vital
status" CDE 2006655, which only matched 1/5). Recommend:
- Remove `CDE:2847330` from `Individual Last Known Disease Status`.
- Add `CDE:2847330` to `Individual Vital Status` instead.
- `Individual Last Known Disease Status` (and `Biospecimen Last Known Disease
  Status`, which has no existing CDE either) still has no good candidate — every
  option returned by the API tops out at a 0.09–0.18 PV-match ratio against
  unrelated domains (gene alterations, lab-urine-protein status, HL7 FHIR
  intervention status). **Leave unmapped; needs a manual caDSR search** (a TCGA-style
  "Person Neoplasm Cancer Status" CDE, if one exists, would be a better target).

## 2. New-annotation proposals (attributes with no existing CDE)

**Accept — real semantic fit, worth adding to the model:**

| Attribute | Recommended CDE | Confidence |
|---|---|---|
| Image Immersion Type | 8058286 v2 Imaging Procedure Microscope Immersion Medium Type | High — exact, HTAN |
| Biospecimen Acquisition Method | 6626651 v2 Biospecimen Acquisition Method Type | High — exact, 100% PV match |
| Image Pyramidal | 7788945 v2 Imaging Pyramid Representation True False Indicator | High — exact, 100% PV match |
| Model Site of Origin | 14156279 v2 Disease Anatomic Site ICD-O-3 Site Label Text | High — 100% PV match |
| Channel Antibody Name | 2004006 v5 Antibody Name | High — exact |
| Channel Antibody Clone | 14767258 v1 Imaging Multiplex Imaging Clone Unique Identifier | High — exact |
| Channel Antibody Lot | 6390920 v1 Lot Number | Medium-high |
| Individual Vital Status | 2847330 v1 Participant Vital Status Type (see §1 misfile note — prefer this over the API's own top pick) | High — 100% PV match |
| Dataset File Formats | 11416926 v2 Data File Format Type (same CDE validated elsewhere as an "agree" case for File Format) | High |
| GeoMx DSP Assay Type | 7789196 v2 Assay Type (same CDE validated elsewhere as an "agree" case for Image Assay Type) | Medium-high |
| Biospecimen / Individual Known Metastasis Sites | 2856440 v3 Tumor Location Anatomic Site Name | Medium — 53% PV match |
| Institution Location State | 7539999 v1 Address State Name | Medium — 90% PV match, administrative |
| Channel Antibody Catalog Number | 2192897 v1 Medical Device Manufacturer Index Number | Medium |
| Channel Antibody Vendor | 2866141 v1 Equipment Manufacturer Name Text | Medium |
| Tool Entity Role | 2201713 v2 Person Affiliation Role Text Type | Medium |
| Grant Institution Name / Alias | 5798571 v1 MCL Contributing Institution Name | Low-medium — generic institution-name placeholder |
| Dataset/File/DSP Dataset Species | 6951303 v1 Data Collection Species Type | Low-medium — right concept, PV encoding likely differs |
| Dataset/File/Publication/DSP Dataset Tumor Type | 6407343 v1 Malignant Neoplasm Anatomic Type | Low-medium — curator should double check |

**Reject — wrong domain, homonym collision, or too generic to add value:**

- `Resource Primary Format` → "Media Type" (65% off) is actually about **specimen
  culture medium**, not file/resource media type — classic homonym trap.
- `GeoMx Scan Height` → "Height" is a **patient vital-sign** CDE (CDISC body
  height), not image scan dimensions — homonym trap.
- `Biospecimen`/`Individual Tumor Subtype`, `NIH RePORTER Link`, `Visium Spatial
  Library Construction Method` → all landed on CDE 2003837 "Result" — a
  content-free generic "text description of a procedure result."
- `GeoMx Sequencing Saturation`, `Image Summary Statistic`, `Tool Cmd`, `Tool
  Operation` → all landed on CDE 6944747 "Function" — same vacuous
  "outcome of the test as originally received" filler CDE.
- `Visium Proportion Reads Mapped to Transcriptome` → CDE 6944736 "Transcript,"
  same filler-CDE family (identical definition text to "Function" above).
- The entire generic **Date/Time/Comment cluster** — `Biospecimen Age at
  Collection Unit`, `Timepoint Type`, `Timepoint Offset`; `datePublished`;
  `File Longitudinal Group/Event Type/Time Elapsed Unit/Sequential/Total`;
  `Grant Start/End Date`; `Embargo End Date`; `Individual Days to Last
  Followup/To Recurrence/to Last Known Disease Status/to Treatment`; `Model Days
  to Treatment`; `NGS RNA RIN`; `publicationMoratorium`; `timeLimitOnUse`; `MOR`;
  `DSP Planned Upload/Release Date`; `Tool Date Last Modified/Release Date`;
  `Visium Permeabilization Time`; `Tool Documentation/Download/Function/Link
  Note` (→ "Comment") — all matched a bare datatype CDE ("Date," "Time,"
  "Comment") that carries zero domain specificity. Adding these would not
  improve the model.
- `Biospecimen Type`, `Biospecimen Species`, `Biospecimen Pathology`,
  `Biospecimen`/`Model Disease Type`, `Biospecimen Last Known Disease Status`,
  `countryOfOrigin`, `measurementTechnique`, `species`, `Dataset/File/Publication
  Assay`, `Resource Topic/Primary Audience/Intended Use/License`, `Tool
  Documentation Type/Download Type/Language/Link Type`, `Image Working Distance
  Unit` — each resolves to a CDE from a clearly different domain (radiation
  therapy, adverse-event reporting, drug dosage units, surgical procedures,
  gene-panel codes, etc.) that shares only a coincidental keyword.

## 3. Low-score (<70) and no-candidate buckets

130 attributes scored ≥70 (reviewed above); 233 scored <70; 211 got no candidate
at all. Spot-checked ~15 of the <70 bucket across NGS QC metrics, licensing, and
administrative fields (`NGS Aligned Reads`→"Race Category Text", `NGS RNA
DV200`→"Necrotic Bone Lesion Text", `GeoMx Nuclei count`→"Prior Surgery TUR
Treatment Count") — uniformly coincidental single-word collisions with unrelated
clinical-trial CDEs. None of the 29 disagreements fall in this band, so nothing
here contradicts an existing annotation. **Recommend leaving the whole <70 and
no-candidate buckets as-is** — not worth per-attribute curation from this run.

## 4. Systemic patterns (for future cde-mapper runs)

1. **Score alone is not reliable.** Cross-check `pv_match_ratio`; a high score
   with a near-zero ratio is a strong signal of a false positive, even when the
   long name sounds plausible.
2. **The API's own #1-ranked candidate isn't always the best of its own list.**
   `Individual Vital Status` is the clearest case: rank-1 had a 1/5 PV match,
   rank-2 had 5/5. Worth a re-rank-by-PV-ratio pass on the full candidate list
   (not just the top hit) whenever the source attribute has permissible values.
3. **Homonym collisions recur**: "Media Type" (culture medium vs. file media),
   "Height" (patient vital sign vs. image dimension). Any CDE whose definition
   domain (clinical vital signs, specimen culture) doesn't match the model's
   domain (imaging, spatial assay) should be discounted regardless of score.
4. **Filler CDEs** ("Date," "Time," "Comment," "Result," "Function," "Category")
   exist in caDSR as near-universal generic elements and will keyword-match
   almost any field whose description contains that word. They add no domain
   value and should probably be excluded from consideration for a
   biology/cancer-research model like this one.
5. Independent of the matcher: **at least 5 `CDE:` values already in the repo are
   invalid or unrelated** (see §0) — these were never verified against caDSR and
   should be corrected before the next `make convert`.
