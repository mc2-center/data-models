"""Update Valid Values

For every module listed in the mapping file, update the list of
valid values in annotationProperty.csv.
"""

import os

import yaml
import pandas as pd


def main(mapping):
    """Main function."""
    for module, attributes in mapping.items():
        to_update = os.path.join("modules", module, "annotationProperty.csv")
        df = (pd.read_csv(to_update, dtype=str, keep_default_na=False)
              .set_index('Attribute'))
        # Replace list of controlled-vocabulary terms with latest of a given attribute.
        for attribute in attributes:
            cv_terms = (pd.read_csv(os.path.join("modules", attribute['src']), dtype=str)
                        .Attribute
                        .tolist())
            df.loc[attribute['name'], 'Valid Values'] = ", ".join(cv_terms)
        df.reset_index().to_csv(to_update, index=False)


if __name__ == "__main__":
    # Get mappings as a dict, where
    #   key = module name
    #   value = list of attributes with valid value to update
    mappings = yaml.safe_load(open("modules/mapping.yaml"))
    main(mappings)
