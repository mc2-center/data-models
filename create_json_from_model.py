from synapseclient import Synapse
from synapseclient.extensions.curator import generate_jsonschema
import sys

from scripts.enum_display_labels import postprocess_schema_files

DATA_MODEL_SOURCE = "mc2.model.csv"
DATA_TYPE = sys.argv[1:] if len(sys.argv) > 1 else None
OUTPUT_DIRECTORY = "./json_schemas"
JSONLD_SOURCE = "mc2.model.jsonld"

syn = Synapse()
syn.login()

schemas, file_paths = generate_jsonschema(
    data_model_source=DATA_MODEL_SOURCE,
    output=OUTPUT_DIRECTORY,
    data_types=DATA_TYPE,
    synapse_client=syn,
)

# Curator's `generate_jsonschema` uses one setting (data_model_labels) for both
# property keys and enum values, so enum values come out as squashed class
# labels (e.g. "RNASequencing") instead of display labels (e.g.
# "RNA Sequencing"). Post-process the schemas just written to rewrite enum
# values back to display-label form, using mc2.model.jsonld as the source of
# truth. Remove this step if/when synapsePythonClient exposes a setting to
# control property-key and enum-value labeling independently.
postprocess_schema_files(file_paths, jsonld_path=JSONLD_SOURCE)
