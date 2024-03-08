## Attribute: Specimen composition

{{ read_csv('shared/specimenComp.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

## Attribute: Specimen type

{{ read_csv('shared/specimenType.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}
