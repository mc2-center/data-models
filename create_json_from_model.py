from synapseclient import Synapse
from synapseclient.extensions.curator import generate_jsonschema

DATA_MODEL_SOURCE = "mc2.model.csv"
DATA_TYPE = ["DataDSP", "Study", "FileView", "PublicationView", "GrantView", "ToolView", "EducationalResource", "DatasetView", "DataCatalog", "Biospecimen", "Individual", "Model"]
OUTPUT_DIRECTORY = "./json_schemas"

syn = Synapse()
syn.login()

schemas, file_paths = generate_jsonschema(
    data_model_source=DATA_MODEL_SOURCE,
    output=OUTPUT_DIRECTORY,
    data_types=DATA_TYPE,
    synapse_client=syn,
)
