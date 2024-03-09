## Attribute: Disease status

<div style="max-height:450px; overflow-x: hidden; overflow-y: auto;">

{{ read_csv('shared/diseaseStatus.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

</div>

## Attribute: Metastasis status

<div style="max-height:450px; overflow-x: hidden; overflow-y: auto;">

{{ read_csv('shared/metStatus.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

</div>
