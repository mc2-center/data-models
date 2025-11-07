CSV := mc2.model.csv

all: collate fix convert

collate:
	@echo "Collating module components..."
	head -1 modules/consortium/annotationProperty.csv > ${CSV}
	tail -n +2 -q modules/*/annotationProperty.csv >> ${CSV}

fix:
	@echo "Modifying columnType to remove string_list"
	awk -F ',' '{ gsub(/string_list/, ""); print }' OFS=',' ${CSV} > tmp.csv
	mv tmp.csv ${CSV}

convert:
	schematic schema convert ${CSV}