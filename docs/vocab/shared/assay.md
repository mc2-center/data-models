## Attribute: Assay

{{ read_csv('shared/assay.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}

## Attribute: Image assay

{{ read_csv('shared/imageAssay.csv', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}