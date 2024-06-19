"""Update Valid Values

For every module listed in the mapping file, update the list of valid
values in annotationProperty.csv.  This will also generate a file
containing the full list of valid values for the data models.
"""

import os

import pandas as pd
import yaml

PARENT_DIR = "modules"


def main(mapping):
    """Main function."""
    all_terms = pd.DataFrame(
        columns=["category", "valid_value", "nonpreferred_values"]
    )
    for module, attributes in mapping.items():
        to_update = os.path.join(PARENT_DIR, module, "annotationProperty.csv")

        # Read all columns as strings, so that `TRUE/FALSE` values are
        # not rewritten as `True/False`. NaN values should also not be
        # used.
        df = (
            pd.read_csv(to_update, dtype=str, keep_default_na=False)
            .set_index("Attribute")
        )

        for attribute in attributes:
            cv_file = os.path.join(PARENT_DIR, attribute["src"])
            cv_df = pd.read_csv(
                cv_file, dtype=str,
                keep_default_na=False,
                usecols=["Attribute", "Nonpreferred Terms"]
            )
            cv_terms = cv_df["Attribute"].tolist()
            cv_nonpreferred = cv_df["Nonpreferred Terms"].tolist()

            # Replace list of valid values in annotationProperty file
            # with latest terms for the given attribute.
            df.loc[attribute["name"], "Valid Values"] = ", ".join(cv_terms)

            # Add latest terms to list of all valid values.
            terms_to_add = pd.DataFrame()
            terms_to_add["valid_value"] = cv_terms
            terms_to_add["nonpreferred_values"] = cv_nonpreferred
            terms_to_add["category"] = os.path.basename(cv_file).split(".")[0]
            all_terms = pd.concat([all_terms, terms_to_add])
        df.to_csv(to_update)
    all_terms.drop_duplicates().to_csv("all_valid_values.csv", index=False)


if __name__ == "__main__":
    with open(os.path.join(PARENT_DIR, "mapping.yaml")) as f:
        mapping_cfg = yaml.safe_load(f)
    main(mapping_cfg)
