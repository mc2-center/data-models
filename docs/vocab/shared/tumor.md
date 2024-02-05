## Type

{{ read_csv('shared/tumorType.csv', usecols=['Attribute','Description']) }}

## Subtype

{{ read_csv('shared/tumorSubtype.csv', usecols=['Attribute','Description']) }}

## Grade

{{ read_csv('shared/tumorGrade.csv', usecols=['Attribute','Description']) }}

## Origin

{{ read_csv('shared/tumorOrigin.csv', usecols=['Attribute','Description']) }}
