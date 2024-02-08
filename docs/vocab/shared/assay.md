## General

{{ read_csv('shared/assay.csv', usecols=['Attribute','Description']) }}

## Image-specific

{{ read_csv('shared/imageAssay.csv', usecols=['Attribute','Description']) }}