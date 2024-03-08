## Attribute: Disease status

{{ read_csv('shared/diseaseStatus.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

## Attribute: Metastasis status

{{ read_csv('shared/metStatus.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}