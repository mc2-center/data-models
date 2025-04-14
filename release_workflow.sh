#/usr/bin/bash

#Usage: bash release_workflow.sh <path/to/config.yml> <path/to/model/repo>

#This script will:
#- update controlled vocabulary sets listed in annotationProperty.csv files and the all_valid_values.csv
#- build a model CSV and convert to JSON-LD, using schematic
#- create CSV template files, saving them in a new 'template' folder
#- generate Google Sheet links and save them in a local file 'release_output.txt'

#Intended for use when creating a data model release package.

#Requires: .synapseConfig available in environment, python, schematic 

#Model repo path should contain 'update_valid_values.py' and a 'Makefile' defining how the CSV and JSON-LD are built

config="$1"
homedir="$2"
convert="$3"
datatypes="DataDSP Study FileView PublicationView GrantView ToolView EducationalResource DatasetView PersonView"

cd "$homedir"

mkdir -p $homedir/templates

python update_valid_values.py

if [ $convert = "true" ]; then
	make
fi

for i in $datatypes;
do
	schematic manifest -c "$config" get -dt "$i" -o "$homedir/templates/$i.csv" -s >> release_output.txt || continue
done

#clean up leftover files
rm *.schema.json
rm *.manifest.csv