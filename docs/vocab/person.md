## Attribute: Chair role

{{ read_csv('person/chair_roles.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

## Attribute: Working group participation

{{ read_csv('person/working_group_participation.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}
