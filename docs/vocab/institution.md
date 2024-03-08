## Attribute: Name

{{ read_csv('institution/institution_name.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

## Attribute: Alias

{{ read_csv('institution/institution_alias.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

## Attribute: State location

{{ read_csv('institution/institution_location_state.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}
