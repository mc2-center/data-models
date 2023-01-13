CSV := mc2.model.csv

all: collate convert

collate:
	@echo "Collating module components..."
	head -1 modules/consortium/consortium_funding_agency.csv > ${CSV}
	tail -n +2 -q modules/*/*.csv >> ${CSV}

convert:
	schematic schema convert ${CSV}