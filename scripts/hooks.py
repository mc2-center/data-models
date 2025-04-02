from os.path import join

import pandas as pd
import yaml

# Data models for the documentation site: filename -> page title
DATA_MODELS = {
    "dataset": "Dataset",
    "sharingPlans": "Dataset Sharing Plan",
    "education": "Education Resource",
    "file": "File",
    "grant": "Grant",
    "person": "Person",
    "publication": "Publication",
    "study": "Study",
    "tool": "Tool",
}

COLS_TO_RENDER = [
    "Attribute",
    "Description",
    "Required",
    "Validation Rules",
    "Examples",
]

MAPPING_FILE = join("modules", "mapping.yaml")
NAVIGATION_FILE = "nav.yml"


def generate_linked_model(model: str):
    """Generates a CSV with linked attributes to standard term definitions.

    Desired markdown: render model template so that
        - it is known which attributes require valid values
        - clicking on attribute will direct to valid values table
    """
    parent = join("modules", model)
    annotations_file = join(parent, "annotationProperty.csv")
    example_file = join(parent, "exampleColumn.csv")
    template_file = join(parent, "template.csv")

    # Read both annotation properties and examples
    annotation_df = pd.read_csv(annotations_file, quoting=1).fillna("")
    examples_df = pd.read_csv(example_file, quoting=1).fillna("")

    # First select only the columns we want from annotation_df
    df = annotation_df[
        ["Attribute", "Description", "Required", "Validation Rules", "Valid Values"]
    ]

    # Then add the Example column and rename it to Examples
    df = df.merge(
        examples_df[["Attribute", "Example"]],
        on="Attribute",
        how="left",
    ).rename(columns={"Example": "Examples"})

    # If attribute has a list of valid values, create a link.
    for _, row in df[df["Valid Values"].ne("")].iterrows():
        attr_link = (
            "["
            + row["Attribute"]
            + (
                f"](../valid_values/{model}.md#attribute-"
                f"{row['Attribute'].lower().replace(' ', '-')})"
            )
        )
        df.at[_, "Attribute"] = attr_link

    # For any validation rules with a regex, replace `\` with `\\`
    # for proper rendering.
    df["Validation Rules"] = df["Validation Rules"].replace(r"\\", r"\\\\", regex=True)

    # Indicate "None" if there are no validation rules for the attribute.
    df.loc[df["Validation Rules"] == "", "Validation Rules"] = "_None_"

    df[COLS_TO_RENDER].to_csv(template_file, index=False)


def generate_valid_values_markdown(model: str):
    """Generates Markdown page for standard terms of the given data model."""
    parent = join("docs", "valid_values")
    with open(MAPPING_FILE) as f, \
         open(join(parent, f"{model}.md"), "w") as md:
        mapping = yaml.safe_load(f)
        for attribute in mapping[model]:
            name = attribute.get("name")
            file_src = attribute.get("src")
            md.write(f"## Attribute: `{name}`\n\n")
            md.write(
                '<div style="max-height:650px; overflow-x: hidden; overflow-y: auto;">\n\n'
            )
            md.write(
                "{{ read_csv('"
                + file_src
                + "', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}\n\n"
            )
            md.write("</div>\n\n\n")


def on_pre_build(config, **kwargs) -> None:
    """Pre-process data model and valid values files."""
    for model in DATA_MODELS.keys():
        generate_linked_model(model)
        generate_valid_values_markdown(model)


def on_files(_, config) -> None:
    """Updates the documentation site navigation.

    This is a hacky solution to updating the nav configuration
    to include the automated markdown pages created by the
    generate_valid_values_markdown() function.
    """
    with open(NAVIGATION_FILE) as f:
        nav_mapping = yaml.safe_load(f)
    config["nav"] = nav_mapping

    config["nav"]["Standard Terms"] = {
        "All terms": "valid_values/all_terms.md",
        "Terms by model": [],
    }
    for model, title in DATA_MODELS.items():
        config["nav"]["Standard Terms"]["Terms by model"].append(
            {title: join("valid_values", model + ".md")}
        )
