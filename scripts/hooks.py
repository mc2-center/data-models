from os.path import join
import pandas as pd
import numpy as np

DATA_MODELS = [
    "dataset",
    "education",
    "grant",
    "person",
    "publication",
    "tool",
]

COLS_TO_RENDER = [
    'Attribute',
    'Description',
    'Required',
    'Validation Rules'
]

def on_pre_build(config, **kwargs) -> None:
    """Pre-process template files.
    
    Desired markdown: render model template so that
        - it is known which attributes require valid values
        - clicking on attribute will direct to valid values table
    """
    for model in DATA_MODELS:
        parent = join("modules", model)
        df = (
            pd.read_csv(join(parent, 'annotationProperty.csv'))
            .fillna(""))

        # If attribute has a list of valid values, create a link.
        df['Attribute'] = np.where(
            ~df['Valid Values'].eq(""),
            "[" + df['Attribute'] + f"](../valid_values/{model}.md#attribute-dataset-tissue)",
            df['Attribute'])
        
        # For any validation rules with a regex, replace `\` with `\\`
        # for proper rendering.
        df['Validation Rules'] = (
            df['Validation Rules']
            .replace(r"\\", r"\\\\", regex=True))

        # Indicate "None" if there are no validation rules for the attribute.
        df.loc[df['Validation Rules'] == "", "Validation Rules"] = "_None_"

        df[COLS_TO_RENDER].to_csv(join(parent, 'template.csv'), index=False)
