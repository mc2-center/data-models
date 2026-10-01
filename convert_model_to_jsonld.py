from synapseclient import Synapse
from synapseclient.extensions.curator import generate_jsonld

DATA_MODEL_SOURCE = "mc2.model.csv"
OUTPUT_JSONLD = "mc2.model.jsonld"

syn = Synapse()
syn.login()

generate_jsonld(
    schema=DATA_MODEL_SOURCE,
    data_model_labels="class_label",
    output_jsonld=OUTPUT_JSONLD,
    synapse_client=syn,
)
