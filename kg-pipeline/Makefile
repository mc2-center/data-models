PYTHON := python3

CSV_TO_LINKML := scripts/vendor/csv_to_linkml.py
ROOT_MODEL := ../mc2.model.csv
MAPPING := ../modules/mapping.yaml
MODULES_DIR := ../modules

OWLGEN_FLAGS := --skip-vacuous-local-range-axioms \
                --skip-vacuous-min-zero-cardinality-axioms \
                --consolidate-cardinality-axioms

.PHONY: all mc2-model-linkml schema sagecdm-schema extract harmonize suggest-mappings crosswalk-ontology crosswalk-scdm triples link-scdm validate update-coverage-baseline publish-portal-kg test clean \
	extract-mc2-assay harmonize-mc2-assay triples-mc2-assay link-sagebrain publish-mc2-assay \
	extract-datacatalog harmonize-datacatalog triples-datacatalog merge-datacatalog combined-kg full-kg

all: schema extract harmonize triples validate

# --- Stage 0: MC2 data model as LinkML + RDF Turtle ---

# Regenerate schema/mc2_model.linkml.yaml from the upstream MC2 model, using
# the vendored copy of the csv-to-linkml converter (scripts/vendor/) - no
# Claude Code skill installation required, fully reproducible from a clean
# clone. Not a dependency of `schema`/`all` since it only needs to run when
# modules/ changes; commit the result afterward like any other
# generated-but-checked-in artifact (mirrors templates/*.csv at the repo root).
mc2-model-linkml:
	$(PYTHON) $(CSV_TO_LINKML) convert $(ROOT_MODEL) \
		--mapping $(MAPPING) --modules-dir $(MODULES_DIR) \
		--schema-id https://w3id.org/mc2-center/mc2-model --schema-name mc2_model \
		--prefix 'CRDC_CDE=https://cadsrapi.cancer.gov/rad/NCIAPI.v1_0:NciApiRad/DataElement/' \
		--out schema/mc2_model.linkml.yaml
	$(PYTHON) scripts/resolve_prefixes.py schema/mc2_model.linkml.yaml \
		--mapping $(MAPPING) --modules-dir $(MODULES_DIR) \
		--report schema/mc2_model_prefixes_report.md

# Portable step: LinkML -> OWL/Turtle for both schemas. This is what `all`
# actually depends on; CI can run this without any skill dependency as long
# as schema/*.linkml.yaml are already checked in.
schema:
	linkml generate owl -f ttl $(OWLGEN_FLAGS) \
		schema/mc2_model.linkml.yaml > schema/mc2_model.ttl
	linkml generate owl -f ttl --no-mergeimports $(OWLGEN_FLAGS) \
		schema/cckp_portal.linkml.yaml > schema/cckp_portal.ttl
	$(PYTHON) scripts/validate_graph.py --parse-only schema/mc2_model.ttl schema/cckp_portal.ttl

# Generate schema/sagecdm.ttl from the vendored, pinned Sage Common Data
# Model source (schema/vendor/sagecdm/ - see VENDORED.md for the pinned
# commit and re-vendoring instructions). Not a dependency of `schema`/`all`
# for the same reason mc2-model-linkml isn't - only needs to run when the
# vendored SCDM source is deliberately updated; commit the result
# afterward like any other generated-but-checked-in artifact.
sagecdm-schema:
	linkml generate owl -f ttl $(OWLGEN_FLAGS) \
		schema/vendor/sagecdm/sage_cdm.yaml > schema/sagecdm.ttl
	$(PYTHON) scripts/validate_graph.py --parse-only schema/sagecdm.ttl

# --- Stage 2: Extract ---

extract:
	$(PYTHON) scripts/extract_cckp_tables.py --out-dir data/raw --data-sources data_sources.yaml

# --- Stage 3: Harmonize ---

harmonize:
	$(PYTHON) scripts/harmonize.py \
		--schema schema/cckp_portal.linkml.yaml \
		--mapping $(MAPPING) --modules-dir $(MODULES_DIR) \
		--raw-dir data/raw --out-dir data/harmonized --sssom-dir mappings/sssom

# --- Stage 3.5: Suggest candidate mappings for unresolved values (human review only) ---

suggest-mappings:
	$(PYTHON) scripts/suggest_mappings.py \
		--schema schema/cckp_portal.linkml.yaml \
		--mapping $(MAPPING) --modules-dir $(MODULES_DIR) \
		--unmapped-csv data/harmonized/unmapped_terms.csv \
		--out data/harmonized/mapping_suggestions.csv

# --- Supplementary: ontology crosswalks for federation with sagebrain-model ---
# (human review only, never consumed by harmonize.py/build_triples.py)

crosswalk-ontology:
	$(PYTHON) scripts/crosswalk_ontology.py --cv $(MODULES_DIR)/shared/tumorType.csv \
		--target-ontology mondo --out mappings/crosswalks/tumorType_ncit_to_mondo.sssom.tsv
	$(PYTHON) scripts/crosswalk_ontology.py --cv $(MODULES_DIR)/shared/diseaseType.csv \
		--target-ontology mondo --out mappings/crosswalks/diseaseType_ncit_to_mondo.sssom.tsv
	$(PYTHON) scripts/crosswalk_ontology.py --cv $(MODULES_DIR)/shared/diseaseStatus.csv \
		--target-ontology mondo --out mappings/crosswalks/diseaseStatus_ncit_to_mondo.sssom.tsv
	$(PYTHON) scripts/crosswalk_ontology.py --cv $(MODULES_DIR)/shared/tissue.csv \
		--target-ontology uberon --out mappings/crosswalks/tissue_ncit_to_uberon.sssom.tsv

# --- Supplementary: institution/consortium crosswalks for federation with
# SCDM (Sage Common Data Model) --- (see plans/scdm_alignment.md). The
# institution crosswalk is deterministic (a ROR id already is the
# organization's identity); the consortium crosswalk ships reviewed=false
# and needs human curation before scripts/link_scdm.py will mint from it -
# see scripts/crosswalk_scdm.py's docstring for why.

crosswalk-scdm:
	$(PYTHON) scripts/crosswalk_scdm.py \
		--institution-cv $(MODULES_DIR)/institution/institution_name.csv \
		--institution-alias-cv $(MODULES_DIR)/institution/institution_alias.csv \
		--consortium-cv $(MODULES_DIR)/consortium/consortium_name.csv \
		--organization-out mappings/crosswalks/institution_to_scdm_organization.tsv \
		--program-out mappings/crosswalks/consortium_to_scdm_program.tsv

# --- Stage 4: Map to RDF ---

triples:
	$(PYTHON) scripts/build_triples.py \
		--schema schema/cckp_portal.linkml.yaml \
		--mc2-schema schema/mc2_model.linkml.yaml \
		--harmonized-dir data/harmonized --out-dir data/rdf \
		--merge-with schema/mc2_model.ttl schema/cckp_portal.ttl \
		--merged-out data/rdf/cckp_kg.ttl \
		--confirmed-unmappable mappings/confirmed_unmappable.tsv

# Links the public CCKP-portal graph to SCDM Organization/Program/
# provisional-Person entities - see scripts/link_scdm.py's docstring. Own
# target, not folded into `make all`/`triples`: consortium_to_scdm_program.tsv
# ships reviewed=false until a human curates it, so this currently mints 0
# Program nodes/edges by design (Organization nodes/edges mint every run -
# no review gate needed there). Output stays a separate file
# (data/rdf/scdm_links.ttl), not merged into cckp_kg.ttl, matching how
# data/mc2_assay/rdf/sagebrain_links.ttl stays separate from
# mc2_assay_kg.ttl rather than being folded in.
link-scdm:
	$(PYTHON) scripts/link_scdm.py \
		--harmonized-dir data/harmonized \
		--organization-crosswalk mappings/crosswalks/institution_to_scdm_organization.tsv \
		--program-crosswalk mappings/crosswalks/consortium_to_scdm_program.tsv \
		--out data/rdf/scdm_links.ttl

# --- Supplementary: Data Catalog annotations (native Synapse Dataset entity
# annotations - measurementTechnique, license, ... - distinct from the CCKP
# portal's own Dataset schema) --- (see plans/datacatalog_kg_integration.md).
# Own targets, not folded into `make all`/`harmonize`/`triples`: a new,
# not-yet-broadly-verified stage, and several fields (accessType,
# downloadType, dataType) have large, expected, permanent unmapped counts
# that would badly skew the main 5-class coverage-baseline ratchet if they
# shared its harmonize run - hence the separate --out-dir below (same reason
# harmonize-mc2-assay uses its own data/mc2_assay/harmonized/, just staying
# in the public data/ tree here since this data is public, unlike mc2_assay).

extract-datacatalog:
	$(PYTHON) scripts/extract_datacatalog.py --out-dir data/raw --data-sources data_sources.yaml

harmonize-datacatalog:
	$(PYTHON) scripts/harmonize.py \
		--schema schema/mc2_model.linkml.yaml \
		--mapping $(MAPPING) --modules-dir $(MODULES_DIR) \
		--raw-dir data/raw --out-dir data/harmonized/datacatalog --sssom-dir mappings/sssom \
		--classes "DataCatalog"

triples-datacatalog:
	$(PYTHON) scripts/build_datacatalog_triples.py \
		--harmonized-dir data/harmonized/datacatalog --mc2-schema schema/mc2_model.linkml.yaml \
		--out data/rdf/DataCatalog.ttl

# Folds data/rdf/DataCatalog.ttl into data/rdf/cckp_kg.ttl IN PLACE - a
# separate, explicit step (not automatic) until this stage has been run and
# reviewed at least once. Safe to re-run; see scripts/merge_datacatalog.py's
# docstring. CAUTION: `make triples` rebuilds data/rdf/cckp_kg.ttl from
# scratch without DataCatalog, so re-running `triples` after this silently
# drops the merge again - if you want a merge that survives that, use
# `combined-kg` below instead, which writes to its own separate output file.
merge-datacatalog:
	$(PYTHON) scripts/merge_datacatalog.py --cckp-kg data/rdf/cckp_kg.ttl --datacatalog data/rdf/DataCatalog.ttl

# Same merge as `merge-datacatalog`, but as a self-contained, dependency-safe
# target: rebuilds both data/rdf/cckp_kg.ttl (via `triples`) and
# data/rdf/DataCatalog.ttl (via `triples-datacatalog`) fresh, then merges
# them into their OWN output file, data/rdf/cckp_kg_with_datacatalog.ttl,
# rather than overwriting cckp_kg.ttl in place - so cckp_kg.ttl stays exactly
# what `make triples` alone produces (no DataCatalog), and this file is
# always the current, complete combined graph, never silently stale. Not a
# dependency of `all` - DataCatalog stays opt-in for the same reason
# `merge-datacatalog` above is (see "Supplementary: Data Catalog" comment).
combined-kg: triples triples-datacatalog
	$(PYTHON) scripts/merge_datacatalog.py --cckp-kg data/rdf/cckp_kg.ttl --datacatalog data/rdf/DataCatalog.ttl \
		--out data/rdf/cckp_kg_with_datacatalog.ttl
	$(PYTHON) scripts/validate_graph.py --shacl schema/cckp_portal.shacl.ttl data/rdf/cckp_kg_with_datacatalog.ttl

# The fullest public-portal graph: combined-kg (base + DataCatalog) with
# scdm_links.ttl's SCDM Organization/Program/Person nodes and
# institutionRef/consortiumRef/investigatorRef/contributorRef edges folded
# in too, via the generic scripts/merge_ttl.py (scdm_links.ttl reuses the
# same subject IRIs as edge sources, so this is a plain triple-set union,
# same as combined-kg's own DataCatalog merge - see "Consuming the graph" in
# README.md). Own output file, data/rdf/cckp_kg_full.ttl - doesn't change
# combined-kg's own output, so anyone relying on cckp_kg_with_datacatalog.ttl
# NOT having SCDM's tier-2/derived-not-authoritative data mixed in is
# unaffected. Not a dependency of `all` - same opt-in reasoning as
# `link-scdm`/`combined-kg` above.
full-kg: combined-kg link-scdm
	$(PYTHON) scripts/merge_ttl.py --base data/rdf/cckp_kg_with_datacatalog.ttl --overlay data/rdf/scdm_links.ttl \
		--out data/rdf/cckp_kg_full.ttl
	$(PYTHON) scripts/validate_graph.py --shacl schema/cckp_portal.shacl.ttl data/rdf/cckp_kg_full.ttl

# --- Stage 5: Validate ---

validate:
	$(PYTHON) scripts/validate_graph.py --coverage data/harmonized/unmapped_terms.csv data/rdf/*.ttl \
		--baseline mappings/coverage_baseline.json --fail-on-regression
	$(PYTHON) scripts/validate_graph.py --shacl schema/cckp_portal.shacl.ttl data/rdf/cckp_kg.ttl

# Run after intentionally curating a CV or knowingly accepting a new gap, to
# move the mappings/coverage_baseline.json ratchet forward. Committed (unlike
# data/harmonized/*, which is gitignored) so the ratchet persists across runs.
update-coverage-baseline:
	$(PYTHON) scripts/validate_graph.py --coverage data/harmonized/unmapped_terms.csv data/rdf/*.ttl \
		--update-baseline mappings/coverage_baseline.json

# Uploads data/{raw,harmonized,rdf}/ (the public CCKP portal KG) to its
# Synapse staging location (default target: syn76958235, "portal-ttl-builds")
# as new file versions - public data, so no ACL check is performed. See
# scripts/publish_kg.py's docstring.
publish-portal-kg:
	$(PYTHON) scripts/publish_kg.py --profile portal

test:
	pytest test/

clean:
	rm -f data/raw/*.csv data/harmonized/*.csv data/rdf/*.ttl

# --- MC2 assay-metadata KG (biospecimen/individual/model/sequencing/imaging) ---
#
# Deliberately NOT part of `all`/`harmonize`/`triples`/`validate` above, and
# never writes into data/raw|harmonized|rdf/ - this data may be
# access-restricted (per-file Synapse annotations that can require login),
# unlike the public CCKP portal tables the rest of this Makefile builds. See
# "Interoperating with sagebrain-model" in README.md.
#
# Class names match schema/mc2_model.linkml.yaml exactly (including spaces) -
# quoted individually so `make` passes each as one argv entry to --classes.
MC2_ASSAY_CLASSES := "Biospecimen" "Individual" "Model" "Study" "Collection" "File View" \
	"Sequencing Level 1" "Sequencing Level 2" "Sequencing Level 3" "Sequencing RNA Level 1" \
	"Imaging Level 1" "Imaging Level 2" "Imaging Level 3 Image" "Imaging Level 3 Segments" "Imaging Level 4" \
	"Imaging Channel" "NanoString GeoMx DSP Level 1" "NanoString GeoMx DSP Level 2" \
	"NanoString GeoMx DSP Level 3" "NanoString GeoMX ROI Segment Annotation" \
	"NanoString GeoMx DSP Imaging" "NanoString GeoMx Auxiliary Files"

extract-mc2-assay:
	$(PYTHON) scripts/extract_mc2_assay_metadata.py \
		--schema schema/mc2_model.linkml.yaml \
		--mapping $(MAPPING) --modules-dir $(MODULES_DIR) \
		--dataset-csv data/raw/Dataset.csv \
		--out-dir data/mc2_assay/raw

harmonize-mc2-assay:
	$(PYTHON) scripts/harmonize.py \
		--schema schema/mc2_model.linkml.yaml \
		--mapping $(MAPPING) --modules-dir $(MODULES_DIR) \
		--raw-dir data/mc2_assay/raw --out-dir data/mc2_assay/harmonized --sssom-dir mappings/sssom \
		--classes $(MC2_ASSAY_CLASSES)

triples-mc2-assay:
	$(PYTHON) scripts/build_triples.py \
		--schema schema/mc2_model.linkml.yaml \
		--mc2-schema schema/mc2_model.linkml.yaml \
		--harmonized-dir data/mc2_assay/harmonized --out-dir data/mc2_assay/rdf \
		--merged-out data/mc2_assay/rdf/mc2_assay_kg.ttl \
		--classes $(MC2_ASSAY_CLASSES)

# Links the File View graph above into sagebrain-model's own classes/
# properties (biolink:MaterialSample, sagebrain:source_tissue/has_pathology)
# - see scripts/link_sagebrain.py's docstring for what's honestly derivable
# from file-level annotations alone vs. what would need the DCC's upstream
# Biospecimen/Individual/Model tables.
link-sagebrain:
	$(PYTHON) scripts/link_sagebrain.py \
		--file-view-harmonized "data/mc2_assay/harmonized/File View_harmonized.csv" \
		--out data/mc2_assay/rdf/sagebrain_links.ttl

# Uploads data/mc2_assay/{raw,harmonized,rdf}/ to the private/team-restricted
# Synapse staging location (default target: syn76957723, "data-ttl-builds"
# under the "CCKP Knowledge Graph - Staging" project) as new file versions -
# refuses to upload if that target's effective ACL isn't actually
# restricted. See scripts/publish_kg.py's docstring.
publish-mc2-assay:
	$(PYTHON) scripts/publish_kg.py --profile mc2-assay
