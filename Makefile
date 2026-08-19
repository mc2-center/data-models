CSV := mc2.model.csv
QC := ./qc_model/mc2_qc.model.csv
DATA := DataDSP Study FileView PublicationView GrantView ToolView EducationalResource DatasetView DataCatalog Biospecimen Model Individual SequencingLevel1 SequencingLevel2 SequencingLevel3 SequencingRNALevel1 ImagingLevel1 ImagingLevel2 ImagingLevel3Image ImagingLevel3Segments ImagingLevel4 NanoStringGeoMxAuxiliaryFiles NanoStringGeoMxDSPImaging NanoStringGeoMxDSPLevel1 NanoStringGeoMxDSPLevel2 NanoStringGeoMxDSPLevel3 NanoStringGeoMXROISegmentAnnotation 10xVisiumAuxiliaryFiles 10xVisiumRNALevel1 10xVisiumRNALevel2 10xVisiumRNALevel3 10xVisiumRNALevel4

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
	python create_json_from_model.py ${DATA}