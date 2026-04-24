CSV := mc2.model.csv
QC := ./qc_model/mc2_qc.model.csv
DATA := DataDSP Study FileView PublicationView GrantView ToolView EducationalResource DatasetView DataCatalog

all: collate generate-json

qc: collate qc_convert

collate:
	@echo "Collating module components..."
	python update_valid_values.py
	head -1 modules/consortium/annotationProperty.csv > ${CSV}
	tail -n +2 -q modules/*/annotationProperty.csv >> ${CSV}

convert:
	schematic schema convert ${CSV}

qc_convert:
	schematic schema convert ${QC}

generate-json:
	python create_json_from_model.py