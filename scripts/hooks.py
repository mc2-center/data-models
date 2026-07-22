import json
import re
from os.path import getsize, isfile, join

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
    "biospecimen": "Biospecimen",
    "individual": "Individual",
    "model": "Model",
    "imagingChannel": "Imaging Channel",
    "imagingLevel1": "Imaging Level 1",
    "imagingLevel2": "Imaging Level 2",
    "imagingLevel3Image": "Imaging Level 3 (Image)",
    "imagingLevel3Segments": "Imaging Level 3 (Segments)",
    "imagingLevel4": "Imaging Level 4",
    "geomxAux": "NanoString GeoMx Auxiliary Files",
    "geomxImaging": "NanoString GeoMx Imaging",
    "geomxLevel1": "NanoString GeoMx Level 1",
    "geomxLevel2": "NanoString GeoMx Level 2",
    "geomxLevel3": "NanoString GeoMx Level 3",
    "geomxRoi": "NanoString GeoMx ROI Segment Annotation",
    "sequencingLevel1": "Sequencing Level 1",
    "sequencingLevel2": "Sequencing Level 2",
    "sequencingLevel3": "Sequencing Level 3",
    "sequencingRNALevel1": "Sequencing RNA Level 1",
    "visiumRNAAux": "10x Visium Auxiliary Files",
    "visiumRNALevel1": "10x Visium RNA Level 1",
    "visiumRNALevel2": "10x Visium RNA Level 2",
    "visiumRNALevel3": "10x Visium RNA Level 3",
    "visiumRNALevel4": "10x Visium RNA Level 4",
}

# Each model's exported JSON Schema is the authoritative list of which
# attributes actually belong to its manifest (resolved from DependsOn when
# the schema was generated) - map module folder -> json_schemas/<name>.json.
# Only listed where it differs from the module folder name itself.
SCHEMA_COMPONENT = {
    "dataset": "DatasetView",
    "sharingPlans": "DataDSP",
    "education": "EducationalResource",
    "file": "FileView",
    "grant": "GrantView",
    "person": "PersonView",
    "publication": "PublicationView",
    "tool": "ToolView",
    "geomxAux": "NanoStringGeoMxAuxiliaryFiles",
    "geomxImaging": "NanoStringGeoMxDSPImaging",
    "geomxLevel1": "NanoStringGeoMxDSPLevel1",
    "geomxLevel2": "NanoStringGeoMxDSPLevel2",
    "geomxLevel3": "NanoStringGeoMxDSPLevel3",
    "geomxRoi": "NanoStringGeoMXROISegmentAnnotation",
    "visiumRNAAux": "VisiumAuxiliaryFiles",
}

# Columns to render for the full field reference tables.
COLS_TO_RENDER = [
    "Attribute",
    "Description",
    "Required",
    "Key",
    "CDE",
    "Column Type",
    "Format",
    "Pattern",
    "Standard Terms",
    "Examples",
]

# Columns to render for the standard-terms (valid values) tables.
TERMS_COLS_TO_RENDER = ["Valid Value", "Description", "Nonpreferred Terms", "Ontology Term"]

MAPPING_FILENAME = "mapping.yaml"
NAVIGATION_FILENAME = "nav.yml"
MODEL_CSV_FILENAME = "mc2.model.csv"
SCHEMA_DIR = "json_schemas"
ANNOTATIONS_FILENAME = "annotationProperty.csv"
EXAMPLE_FILENAME = "exampleColumn.csv"
REFERENCE_FILENAME = "reference.csv"
TERMS_SUFFIX = ".rendered.csv"


# --- Helper Functions ---
def _create_markdown_link(attribute: str, model: str, text: str = None) -> str:
    """Create markdown link to list of valid values for the given attribute."""
    link_prefix = f"../valid_values/{model}.md#attribute"
    slug = attribute.lower().replace(" ", "-")
    return f"[{text or attribute}]({link_prefix}-{slug})"


def _format_technical_column(col: pd.Series, escape_backslashes: bool = False) -> pd.Series:
    """Format a technical metadata column, replacing empty strings with '_None_'."""
    if escape_backslashes:
        col = col.str.replace(r"\\", r"\\\\", regex=True)
    return col.replace("", "_None_")


def _extract_key(properties: str) -> str:
    """Extract the primary/foreign key designation from a Properties cell
    (e.g. "CDE:12220014, primary_key" -> "Primary Key")."""
    if "primary_key" in properties:
        return "Primary Key"
    if "foreign_key" in properties:
        return "Foreign Key"
    return "_None_"


def _extract_cde(properties: str) -> str:
    """Extract the CDE reference from a Properties cell, if any."""
    match = re.search(r"CDE:\d+", properties)
    return match.group(0) if match else "_None_"


def _ontology_link(identifier: str, url: str) -> str:
    """Render an ontology term as an HTML link, if a URL is available.

    This table is rendered as raw HTML (tablefmt='html') inside a raw <div>
    block for the scrollable Standard Terms tables, so markdown link syntax
    would never get post-processed - it needs to be a real <a> tag already.
    """
    identifier = identifier.strip()
    url = url.strip()
    if identifier and url:
        return f'<a href="{url}">{identifier}</a>'
    return identifier or "None"


def _render_terms_csv(src: str) -> str:
    """Generate a rendered version of a standard-terms CSV with a computed
    Ontology Term link column, and return its path (relative to the
    table-reader plugin's data_path, i.e. under modules/).

    Source CV files (e.g. biospecimen/acquisitionMethod.csv) are hand-curated
    content and are never overwritten; the rendering is written alongside
    them with a distinct suffix, mirroring the reference.csv convention.
    """
    dest = src[: -len(".csv")] + TERMS_SUFFIX if src.endswith(".csv") else src + TERMS_SUFFIX
    dest_path = join("modules", dest)
    src_path = join("modules", src)

    terms_df = pd.read_csv(
        src_path, quoting=1, dtype=str, keep_default_na=False, encoding="utf-8-sig"
    )
    terms_df["Ontology Term"] = terms_df.apply(
        lambda row: _ontology_link(
            row.get("Ontology Identifier", ""), row.get("Ontology Url", "")
        ),
        axis=1,
    )
    terms_df["Nonpreferred Terms"] = terms_df.get(
        "Nonpreferred Terms", pd.Series([""] * len(terms_df))
    ).replace("", "None")
    terms_df = terms_df.rename(columns={"Attribute": "Valid Value"})
    terms_df[TERMS_COLS_TO_RENDER].to_csv(dest_path, index=False)
    return dest


def _get_model_attributes(model: str) -> list:
    """Get the ordered list of attribute display names that make up a
    model's manifest.

    DependsOn (in the module's own annotationProperty.csv) is the live,
    hand-edited source of truth, but the exported JSON Schema is used to
    cross-check it, since either can drift independently: DependsOn can
    gain attributes a schema hasn't been regenerated for yet, while an
    un-regenerated schema can still list attributes since removed from
    DependsOn (e.g. Study.json still has ~15 access-requirement fields that
    were moved out to the governance model but never regenerated away).
    Attributes must appear in DependsOn; the schema, when available, is
    used to filter out anything no longer current.
    """
    annotations_file = join("modules", model, ANNOTATIONS_FILENAME)
    annotation_df = pd.read_csv(
        annotations_file, quoting=1, dtype=str, keep_default_na=False
    )
    # The manifest/root row is the one with a non-empty DependsOn - the
    # only reliable signal (it isn't always the first row, e.g. person's
    # "Person View" row, and IsTemplate isn't consistently set either,
    # e.g. visiumRNALevel1's root row).
    root = annotation_df[annotation_df["DependsOn"].str.strip() != ""].iloc[0]
    depends_on = [a.strip() for a in root["DependsOn"].split(",") if a.strip()]

    component = SCHEMA_COMPONENT.get(model, model[0].upper() + model[1:])
    schema_file = join(SCHEMA_DIR, f"{component}.json")
    if not isfile(schema_file):
        return depends_on

    with open(schema_file) as f:
        schema = json.load(f)
    schema_titles = {prop.get("title", key) for key, prop in schema["properties"].items()}
    return [a for a in depends_on if a in schema_titles]


def _load_attribute_owners() -> dict:
    """Reverse-lookup: which model's valid-values page a given attribute's
    standard-terms anchor actually lives on.

    Attributes are often shared across models via DependsOn (e.g. "File
    Assay" is used by several imaging/sequencing/spatial modules), but its
    anchor is only ever generated on the one model mapping.yaml lists it
    under.
    """
    with open(join("modules", MAPPING_FILENAME)) as f:
        mapping = yaml.safe_load(f)
    return {
        attribute["name"]: owning_model
        for owning_model, attributes in mapping.items()
        for attribute in attributes
    }


# --- Core logic functions ---
def generate_linked_table(model: str):
    """Generate CSV with linked attributes to list of valid values.

    Desired markdown look: render model reference table so that
        - it is known which attributes require valid values
        - clicking on attribute will direct to valid values table

    The attribute list comes from the model's JSON Schema (its DependsOn-
    resolved manifest), and every attribute's metadata is looked up from the
    fully collated mc2.model.csv, since attributes referenced via DependsOn
    (e.g. "Study Key") are often defined in a different module's file than
    the one requesting them.
    """
    parent = join("modules", model)
    example_file = join(parent, EXAMPLE_FILENAME)
    reference_file = join(parent, REFERENCE_FILENAME)

    model_df = (
        pd.read_csv(MODEL_CSV_FILENAME, quoting=1, dtype=str, keep_default_na=False)
        .drop_duplicates(subset="Attribute", keep="first")
        .set_index("Attribute")
    )

    table = pd.DataFrame({"Attribute": _get_model_attributes(model)})
    table = table.merge(
        model_df[[
            "Description", "Required", "Valid Values", "Properties",
            "columnType", "Format", "Pattern",
        ]],
        left_on="Attribute",
        right_index=True,
        how="left",
    ).fillna("").rename(columns={"columnType": "Column Type"})

    # Normalize Required to explicit True/False (rather than blank/NaN).
    table["Required"] = table["Required"].apply(
        lambda v: "True" if str(v).strip() == "True" else "False"
    )

    # Surface primary/foreign key designations and CDE mappings, both
    # encoded together in the Properties column (e.g. "CDE:12220014,
    # primary_key").
    table["Key"] = table["Properties"].apply(_extract_key)
    table["CDE"] = table["Properties"].apply(_extract_cde)

    # Add the Example column and rename it to Examples, if example data
    # exists for this model. Some newer modules don't yet have curated
    # examples, in which case the column is left blank.
    if isfile(example_file):
        examples_df = pd.read_csv(example_file, quoting=1).fillna("")
        table = table.merge(
            examples_df[["Attribute", "Example"]],
            on="Attribute",
            how="left",
        ).rename(columns={"Example": "Examples"})
    else:
        table["Examples"] = ""
    table["Examples"] = table["Examples"].fillna("")

    # If an attribute has a list of standard terms, link to its anchor on
    # whichever model's valid-values page actually owns it.
    attribute_owners = _load_attribute_owners()
    table["Standard Terms"] = table.apply(
        lambda row: (
            _create_markdown_link(
                row["Attribute"], attribute_owners.get(row["Attribute"], model), text="View"
            )
            if row["Valid Values"]
            else "None"
        ),
        axis=1,
    )

    # Fix any remaining rendering issues, then output table as CSV.
    table["Column Type"] = _format_technical_column(table["Column Type"])
    table["Format"] = _format_technical_column(table["Format"])
    table["Pattern"] = _format_technical_column(table["Pattern"], escape_backslashes=True)
    table[COLS_TO_RENDER].to_csv(reference_file, index=False)


def generate_valid_values_markdown(model: str):
    """Generate docs page for standard terms of the given data model.

    Some models have no attributes with a controlled list of standard terms
    (i.e. no entry in mapping.yaml). Skip writing a page for those, so they
    don't show up as an empty, un-linked orphan page in the built site.
    """
    dest_parent_dir = join("docs", "valid_values")

    with open(join("modules", MAPPING_FILENAME)) as f:
        mapping = yaml.safe_load(f)

    if not mapping.get(model):
        return

    with open(join(dest_parent_dir, f"{model}.md"), "w") as md:
        # Create a section in the docs page for each attribute that has a list
        # of standard terms.
        for attribute in mapping.get(model, {}):
            name = attribute.get("name")
            valid_values_src = attribute.get("src")
            rendered_src = _render_terms_csv(valid_values_src)

            md.write(f"## Attribute: `{name}`\n\n")
            md.write(
                '<div style="max-height:650px; overflow-x: hidden; overflow-y: auto;">\n\n'
            )
            md.write(
                "{{ read_csv('"
                + rendered_src
                + "', keep_default_na=False, tablefmt='unsafehtml') }}\n\n"
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

    # Dynamically add valid_values docs page for each data model to config.nav
    # if the docs page exists and has contents.
    for model, page_title in DATA_MODELS.items():
        docs_page = join("valid_values", f"{model}.md")
        if isfile(join("docs", docs_page)) and getsize(join("docs", docs_page)) > 0:
            config["nav"]["Standard Terms"]["Terms by model"].append(
                {page_title: docs_page}
            )
