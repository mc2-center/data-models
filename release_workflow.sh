#/usr/bin/bash

#Usage: bash release_workflow.sh <path/to/config.yml> <path/to/model/repo>

#This script will:
#- update controlled vocabulary sets listed in annotationProperty.csv files and the all_valid_values.csv
#- build a model CSV and convert to JSON-LD, using schematic
#- create CSV template files, saving them in a new 'template' folder

#Intended for use when creating a data model release package.

#Requires: .synapseConfig available in environment, python, schematic 

#Model repo path should contain 'update_valid_values.py' and a 'Makefile' defining how the CSV and JSON-LD are built

config="$1"
homedir="$2"
datatypes="DataDSP Biospecimen PersonView PublicationView GrantView ToolView EducationalResource NanoStringGeoMxDSPLevel1 NanoStringGeoMxDSPLevel2 NanoStringGeoMxDSPLevel3 NanoStringGeoMxDSPImagingLevel2 NanoStringGeoMXROISegmentAnnotation DatasetView ProjectView"

cd "$homedir"

mkdir -p $homedir/templates

python update_valid_values.py

make

for i in $datatypes;
do
	schematic manifest -c "$config" get -dt "$i" -o "$homedir/templates/$i.csv" || continue
done
