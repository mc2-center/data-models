## Name

{{ read_csv('institution/institution_name.csv', usecols=['Attribute','Description']) }}

## Alias

{{ read_csv('institution/institution_alias.csv', usecols=['Attribute','Description']) }}

## State location

{{ read_csv('institution/institution_location_state.csv', usecols=['Attribute','Description']) }}
