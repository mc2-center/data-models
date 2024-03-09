## Attribute: Name

<div style="max-height:450px; overflow-x: hidden; overflow-y: auto;">

{{ read_csv('institution/institution_name.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

</div>

## Attribute: Alias

<div style="max-height:450px; overflow-x: hidden; overflow-y: auto;">

{{ read_csv('institution/institution_alias.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

</div>

## Attribute: State location

<div style="max-height:450px; overflow-x: hidden; overflow-y: auto;">

{{ read_csv('institution/institution_location_state.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

</div>
