PYTHON := python3

CSV_TO_LINKML := scripts/vendor/csv_to_linkml.py
ROOT_MODEL := ../mc2.model.csv
MAPPING := ../modules/mapping.yaml
MODULES_DIR := ../modules

OWLGEN_FLAGS := --skip-vacuous-local-range-axioms \
                --skip-vacuous-min-zero-cardinality-axioms \
                --consolidate-cardinality-axioms

.PHONY: all mc2-model-linkml schema extract harmonize suggest-mappings crosswalk-ontology triples validate update-coverage-baseline publish-portal-kg test clean \
	extract-mc2-assay harmonize-mc2-assay triples-mc2-assay link-sagebrain publish-mc2-assay

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

# --- Stage 4: Map to RDF ---

triples:
	$(PYTHON) scripts/build_triples.py \
		--schema schema/cckp_portal.linkml.yaml \
		--mc2-schema schema/mc2_model.linkml.yaml \
		--harmonized-dir data/harmonized --out-dir data/rdf \
		--merge-with schema/mc2_model.ttl schema/cckp_portal.ttl \
		--merged-out data/rdf/cckp_kg.ttl \
		--confirmed-unmappable mappings/confirmed_unmappable.tsv

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
MC2_ASSAY_CLASSES := "Biospecimen" "Individual" "Model" "Study" "Collection" \
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
		--modules-dir $(MODULES_DIR) \
		--out data/mc2_assay/rdf/sagebrain_links.ttl

# Uploads data/mc2_assay/{raw,harmonized,rdf}/ to the private/team-restricted
# Synapse staging location (default target: syn76957723, "data-ttl-builds"
# under the "CCKP Knowledge Graph - Staging" project) as new file versions -
# refuses to upload if that target's effective ACL isn't actually
# restricted. See scripts/publish_kg.py's docstring.
publish-mc2-assay:
	$(PYTHON) scripts/publish_kg.py --profile mc2-assay
