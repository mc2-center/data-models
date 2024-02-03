## General

{{ read_csv('shared/diseaseStatus.csv', usecols=['Attribute','Description']) }}

## Metastasis status

{{ read_csv('shared/metStatus.csv', usecols=['Attribute','Description']) }}