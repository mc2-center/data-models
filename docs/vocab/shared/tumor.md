## Attribute: Tumor type

<div style="max-height:450px; overflow-x: hidden; overflow-y: auto;">

{{ read_csv('shared/tumorType.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

</div>

## Attribute: Tumor subtype

<div style="max-height:450px; overflow-x: hidden; overflow-y: auto;">

{{ read_csv('shared/tumorSubtype.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

<div>

## Attribute: Tumor grade

<div style="max-height:450px; overflow-x: hidden; overflow-y: auto;">

{{ read_csv('shared/tumorGrade.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

</div>

## Attribute: Tumor origin

<div style="max-height:450px; overflow-x: hidden; overflow-y: auto;">

{{ read_csv('shared/tumorOrigin.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

</div>
