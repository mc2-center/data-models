from os.path import join

import pandas as pd
import yaml

# --- Configuration ---

# Data models to display on the documentation site: filename -> page title
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

# Columns to render for the full field reference tables.
COLS_TO_RENDER = [
    "Attribute",
    "Description",
    "Required",
    "Validation Rules",
    "Examples",
]

MAPPING_FILENAME = "mapping.yaml"
NAVIGATION_FILENAME = "nav.yml"
ANNOTATIONS_FILENAME = "annotationProperty.csv"
EXAMPLE_FILENAME = "exampleColumn.csv"
REFERENCE_FILENAME = "reference.csv"


# --- Helper Functions ---
def _create_markdown_link(attribute: str, model: str) -> str:
    """Create markdown link to list of valid values for the given attribute."""
    link_prefix = f"../valid_values/{model}.md#attribute"
    slug = attribute.lower().replace(" ", "-")
    return f"[{attribute}]({link_prefix}-{slug})"


def _escape_backslashes(text: str) -> str:
    """Escape backslashes for proper markdown rendering."""
    return text.replace(r"\\", r"\\\\")


def _format_validation_rules(rules: str) -> str:
    """Format validation rules, replacing empty strings with '_None_'."""
    return _escape_backslashes(rules) if rules else "_None_"


# --- Core logic functions ---
def generate_linked_table(model: str):
    """Generate CSV with linked attributes to list of valid values.

    Desired markdown look: render model reference table so that
        - it is known which attributes require valid values
        - clicking on attribute will direct to valid values table
    """
    parent = join("modules", model)
    annotations_file = join(parent, ANNOTATIONS_FILENAME)
    example_file = join(parent, EXAMPLE_FILENAME)
    reference_file = join(parent, REFERENCE_FILENAME)

    # Read both annotation properties and examples
    annotation_df = pd.read_csv(annotations_file, quoting=1).fillna("")
    examples_df = pd.read_csv(example_file, quoting=1).fillna("")

    # First select only the columns we want from annotation_df
    df = annotation_df[[
        "Attribute",
        "Description",
        "Required",
        "Validation Rules",
        "Valid Values",
    ]]

    # Then add the Example column and rename it to Examples
    df = df.merge(
        examples_df[["Attribute", "Example"]],
        on="Attribute",
        how="left",
    ).rename(columns={"Example": "Examples"})

    # If attribute has a list of valid values, create a link.
    df["Attribute"] = df.apply(
        lambda row: (
            _create_markdown_link(row["Attribute"], model)
            if row["Valid Values"]
            else row["Attribute"]
        ),
        axis=1,
    )

    # Fix any remaining rendering issues, such as escaping backslashes.
    # then output table as CSV.
    df["Validation Rules"] = df["Validation Rules"].apply(_format_validation_rules)
    df[COLS_TO_RENDER].to_csv(reference_file, index=False)


def generate_valid_values_markdown(model: str):
    """Generate docs page for standard terms of the given data model."""
    dest_parent_dir = join("docs", "valid_values")

    with open(join("modules", MAPPING_FILENAME)) as f, \
         open(join(dest_parent_dir, f"{model}.md"), "w") as md:
        mapping = yaml.safe_load(f)

        # Create a section in the docs page for each attribute that has a list
        # of standard terms.
        for attribute in mapping[model]:
            name = attribute.get("name")
            valid_values_src = attribute.get("src")

            md.write(f"## Attribute: `{name}`\n\n")
            md.write(
                '<div style="max-height:650px; overflow-x: hidden; overflow-y: auto;">\n\n'
            )
            md.write(
                "{{ read_csv('"
                + valid_values_src
                + "', header=0, names=['Valid Value','Description'], usecols=['Valid Value','Description'], tablefmt='html') }}\n\n"
            )
            md.write("</div>\n\n\n")


# --- MkDocs event hooks ---
def on_pre_build(config):
    """Pre-process docs setup for the data models of interest.

    For each model, generate:
        - a table CSV that links an attribute to its list of standard terms
        - a docs page of the aforementioned list of standard terms
    """
    for model in DATA_MODELS:
        generate_linked_table(model)
        generate_valid_values_markdown(model)


def on_files(_, config):
    """Update docs site navigation after all files are gathered and generated.

    !!! note
    This is a hacky solution to updating config.nav to include the auto-
    generated markdown pages created by generate_valid_values_markdown().
    """
    with open(NAVIGATION_FILENAME) as f:
        nav_mapping = yaml.safe_load(f)

    # Initial setup for config.nav.
    config["nav"] = nav_mapping
    config["nav"]["Standard Terms"] = {
        "All terms": "valid_values/all_terms.md",
        "Terms by model": [],
    }

    # Dynamically add valid_values docs page for each data model to config.nav.
    for model, page_title in DATA_MODELS.items():
        config["nav"]["Standard Terms"]["Terms by model"].append(
            {page_title: join("valid_values", model + ".md")}
        )
