from synapseclient import Synapse
from synapseclient.extensions.curator import generate_jsonschema
import sys

DATA_MODEL_SOURCE = "mc2.model.csv"
DATA_TYPE = sys.argv[1:] if len(sys.argv) > 1 else None
OUTPUT_DIRECTORY = "./json_schemas"

syn = Synapse()
syn.login()

schemas, file_paths = generate_jsonschema(
    data_model_source=DATA_MODEL_SOURCE,
    output=OUTPUT_DIRECTORY,
    data_types=DATA_TYPE,
    synapse_client=syn,
)
