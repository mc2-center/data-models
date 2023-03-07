"""Update Valid Values

For every module listed in the mapping file, update the list of valid
values in annotationProperty.csv.
"""

import os

import yaml
import pandas as pd

PARENT_DIR = "modules"

def main(mapping):
    """Main function."""
    for module, attributes in mapping.items():
        to_update = os.path.join(PARENT_DIR, module, "annotationProperty.csv")

        # Read all columns as strings, so that `TRUE/FALSE` values are
        # not rewritten as `True/False`. NaN values should also not be
        # used.
        df = (pd.read_csv(to_update, dtype=str, keep_default_na=False)
              .set_index('Attribute'))

        # Replace list of valid values with latest terms for the
        # given attribute.
        for attribute in attributes:
            cv_file = os.path.join(PARENT_DIR, attribute['src'])
            cv_terms = (pd.read_csv(cv_file, dtype=str)['Attribute']
                        .tolist())
            df.loc[attribute['name'], 'Valid Values'] = ", ".join(cv_terms)
        df.to_csv(to_update)


if __name__ == "__main__":
    with open(os.path.join(PARENT_DIR, "mapping.yaml")) as f:
        mapping_cfg = yaml.safe_load(f)
    main(mapping_cfg)
