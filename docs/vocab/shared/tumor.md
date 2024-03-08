## Attribute: Tumor type

{{ read_csv('shared/tumorType.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

## Attribute: Tumor subtype

{{ read_csv('shared/tumorSubtype.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

## Attribute: Tumor grade

{{ read_csv('shared/tumorGrade.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

## Attribute: Tumor origin

{{ read_csv('shared/tumorOrigin.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}
