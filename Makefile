CSV := mc2.model.csv
QC := ./qc_model/mc2_qc.model.csv
DATA := DataDSP Study FileView PublicationView GrantView ToolView EducationalResource DatasetView DataCatalog

all: collate fix generate-json

qc: collate fix qc_fix qc_convert

collate:
	@echo "Collating module components..."
	python update_valid_values.py
	head -1 modules/consortium/annotationProperty.csv > ${CSV}
	tail -n +2 -q modules/*/annotationProperty.csv >> ${CSV}

fix:
	@echo "Modifying columnType to remove string_list"
	awk -F ',' '{ gsub(/string_list/, ""); gsub(/^integer/, "number", $$10); gsub(/^integer/, "number", $$11); gsub(/^int/, "num", $$10); gsub(/^int/, "num", $$11); gsub(/^bool$$/, "boolean", $$10); gsub(/^bool$$/, "boolean", $$11); print }' OFS=',' ${CSV} > tmp_${CSV}
	rm ${CSV}
	mv tmp_${CSV} ${CSV}
	
qc_fix:
	awk -F ',' '{ gsub(/matchAtLeastOne.*/, "list like"); print }' OFS=',' ${CSV} > tmp.csv
	mv tmp.csv ${QC}

convert:
	schematic schema convert ${CSV}

qc_convert:
	schematic schema convert ${QC}

generate-json:
	$(foreach d,$(DATA), schematic schema generate-jsonschema -dms ${CSV} -od . -dt $(d);)
	rm *.schema.json