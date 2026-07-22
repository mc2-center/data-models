# Verification Report

- Source: `modules/shared/diseaseType.csv`
- Decisions: `worklists/shared_diseaseType_vocab_decisions.json`

| Row | Term | Identifier | Verdict | Description | Notes |
|-----|------|------------|---------|-------------|-------|
| 0 | Acinar Cell Neoplasms | NCIT:C4197 | match | added | NCIT:C4197 Acinar Cell Neoplasm; confirmed as direct ancestor of Acinar Cell Car… |
| 1 | Adenomas and Adenocarcinomas | NCIT:C7132 | partial | added | NCIT:C7132 Glandular Cell Neoplasm; the ICD-O category 'Adenomas and Adenocarcin… |
| 2 | Adnexal and Skin Appendage Neoplasms | NCIT:C212119 | match | added | NCIT:C212119 Adnexal Neoplasm; confirmed as direct ancestor of multiple skin app… |
| 8 | Epithelial Neoplasms, NOS | NCIT:C3709 | match | added | NCIT:C3709 Epithelial Neoplasm; confirmed as ancestor of numerous carcinomas and… |
| 9 | Fibroepithelial Neoplasms | NCIT:C3743 | match | added | NCIT:C3743 Fibroepithelial Neoplasm; exact label match; definition confirmed fro… |
| 10 | Fibromatous Neoplasms | NCIT:C3042 | partial | added | NCIT:C3042 Fibromatosis; ICD-O 'Fibromatous Neoplasms' (8810-8829) includes fibr… |
| 11 | Germ Cell Neoplasms | NCIT:C3708 | match | added | NCIT:C3708 Germ Cell Tumor; confirmed as ancestor of multiple germ cell tumors; … |
| 12 | Giant Cell Tumors | NCIT:C3055 | match | added | NCIT:C3055 Giant Cell Tumor; confirmed as ancestor of Malignant Tenosynovial Gia… |
| 13 | Gliomas | NCIT:C3059 | match | added | NCIT:C3059 Glioma; standard NCIT term for ICD-O category 9380-9460. |
| 16 | Leukemias | NCIT:C3161 | match | added | NCIT:C3161 Leukemia; confirmed as direct match via OLS search; semantically equi… |
| 17 | Lipomatous Neoplasms | NCIT:C4248 | match | added | NCIT:C4248 Lipomatous Neoplasm; confirmed as direct parent of Liposarcoma in OLS… |
| 20 | Meningiomas | NCIT:C3230 | match | added | NCIT:C3230 Meningioma; standard NCIT term confirmed as ancestor in prior session… |
| 21 | Mesothelial Neoplasms | NCIT:C3786 | match | added | NCIT:C3786 Mesothelial Neoplasm; confirmed as parent of mesothelial tumor types … |
| 25 | Myelodysplastic Syndromes | NCIT:C3247 | match | added | NCIT:C3247 Myelodysplastic Syndrome; exact label match; matches ICD-O category 9… |
| 26 | Myomatous Neoplasms | NCIT:C214799 | match | added | NCIT:C214799 Myomatous Neoplasm; confirmed as direct parent of Myoma (NCIT:C4882… |
| 28 | Neoplasms, NOS | NCIT:C3262 | match | added | NCIT:C3262 Neoplasm; root morphology class; matches ICD-O category 'Neoplasms, N… |
| 29 | Nerve Sheath Tumors | NCIT:C4972 | match | added | NCIT:C4972 Nerve Sheath Neoplasm; confirmed as direct ancestor in OLS search; se… |
| 31 | Nevi and Melanomas | NCIT:C7058 | match | added | NCIT:C7058 Melanocytic Neoplasm; confirmed as ancestor of Benign Conjunctival Me… |
| 32 | Not Applicable | NCIT:C48660 | match | added | NCIT:C48660 Not Applicable; standard NCIT general qualifier. |
| 33 | Not Otherwise Specified | NCIT:C19594 | match | added | NCIT:C19594 Not Otherwise Specified; standard NCIT general qualifier. |
| 34 | Not Reported | NCIT:C43234 | match | added | NCIT:C43234 Not Reported; standard NCIT general qualifier. |
| 35 | Odontogenic Tumors | NCIT:C3286 | match | added | NCIT:C3286 Odontogenic Neoplasm; confirmed as direct ancestor of Dentinogenic Gh… |
| 37 | Paragangliomas and Glomus Tumors | NCIT:C3308 | partial | added | NCIT:C3308 Paraganglioma; confirmed as ancestor of Jugulotympanic Paraganglioma … |
| 38 | Plasma Cell Neoplasm | NCIT:C4665 | match | added | NCIT:C4665 Plasma Cell Neoplasm; confirmed as ancestor of Multiple Myeloma in pr… |
| 39 | Soft Tissue Tumors and Sarcomas, NOS | NCIT:C3377 | partial | added | NCIT:C3377 Soft Tissue Neoplasm; confirmed as ancestor of multiple soft tissue t… |
| 40 | Squamous Cell Neoplasms | NCIT:C3792 | match | added | NCIT:C3792 Squamous Cell Neoplasm; confirmed in prior session searches; matches … |
| 41 | Synovial-like Neoplasms | NCIT:C8964 | match | added | NCIT:C8964 Synovial Neoplasm; confirmed as ancestor of Malignant Tenosynovial Gi… |
| 42 | Thymic Epithelial Neoplasms | NCIT:C6450 | match | added | NCIT:C6450 Thymus Epithelial Neoplasm; confirmed as ancestor of Combined Thymus … |
| 44 | Trophoblastic neoplasms | NCIT:C180633 | partial | added | NCIT:C180633 Gestational Trophoblastic Disorder; the ICD-O 'Trophoblastic neopla… |
| 45 | Unknown | NCIT:C17998 | match | added | NCIT:C17998 Unknown; standard NCIT general qualifier. |

## Summary

- **Total decisions applied:** 30
- **Verified matches:** 25
- **Descriptions added:** 30

## Needs Human Review (5 terms)

- Row 1: **Adenomas and Adenocarcinomas** — `partial`: NCIT:C7132 Glandular Cell Neoplasm; the ICD-O category 'Adenomas and Adenocarcinomas' (8140-8389) covers glandular tumors broadly. NCIT:C7132 is the umbrella morphology class but does not restrict to adenoma/adenocarcinoma subtypes only.
- Row 10: **Fibromatous Neoplasms** — `partial`: NCIT:C3042 Fibromatosis; ICD-O 'Fibromatous Neoplasms' (8810-8829) includes fibromas and fibromatosis. NCIT:C3042 specifically describes fibromatosis; a broader 'Fibromatous Neoplasm' parent class is not a distinct NCIT term.
- Row 37: **Paragangliomas and Glomus Tumors** — `partial`: NCIT:C3308 Paraganglioma; confirmed as ancestor of Jugulotympanic Paraganglioma in OLS search; the vocab term also includes glomus tumors (ICD-O 8711), which are glomangiomas/glomus tumors of soft tissue — a distinct NCIT lineage not captured by C3308.
- Row 39: **Soft Tissue Tumors and Sarcomas, NOS** — `partial`: NCIT:C3377 Soft Tissue Neoplasm; confirmed as ancestor of multiple soft tissue tumors in OLS search. The vocab term implies a broader category including sarcomas specifically; NCIT:C3377 covers both benign and malignant soft tissue tumors.
- Row 44: **Trophoblastic neoplasms** — `partial`: NCIT:C180633 Gestational Trophoblastic Disorder; the ICD-O 'Trophoblastic neoplasms' category (9100-9105) specifically covers neoplasms, while C180633 includes both non-neoplastic and neoplastic trophoblastic conditions. No dedicated 'Trophoblastic Neoplasm' class without the gestational qualifier found in NCIT.
