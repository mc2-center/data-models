PYTHON := python3

CSV_TO_LINKML := $(HOME)/.claude/skills/csv-to-linkml/scripts/csv_to_linkml.py
ROOT_MODEL := ../mc2.model.csv
MAPPING := ../modules/mapping.yaml
MODULES_DIR := ../modules

OWLGEN_FLAGS := --skip-vacuous-local-range-axioms \
                --skip-vacuous-min-zero-cardinality-axioms \
                --consolidate-cardinality-axioms

.PHONY: all mc2-model-linkml schema extract harmonize triples validate test clean

all: schema extract harmonize triples validate

# --- Stage 0: MC2 data model as LinkML + RDF Turtle ---

# Regenerate schema/mc2_model.linkml.yaml from the upstream MC2 model. Not a
# dependency of `schema`/`all` - it shells out to a user-level Claude Code
# skill path, so it isn't portable to CI. Run by hand when modules/ changes,
# then commit the result like any other generated-but-checked-in artifact
# (mirrors templates/*.csv at the repo root).
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

# --- Stage 4: Map to RDF ---

triples:
	$(PYTHON) scripts/build_triples.py \
		--schema schema/cckp_portal.linkml.yaml \
		--mc2-schema schema/mc2_model.linkml.yaml \
		--harmonized-dir data/harmonized --out-dir data/rdf \
		--merge-with schema/mc2_model.ttl schema/cckp_portal.ttl \
		--merged-out data/rdf/cckp_kg.ttl

# --- Stage 5: Validate ---

validate:
	$(PYTHON) scripts/validate_graph.py --coverage data/harmonized/unmapped_terms.csv data/rdf/*.ttl

test:
	pytest test/

clean:
	rm -f data/raw/*.csv data/harmonized/*.csv data/rdf/*.ttl
