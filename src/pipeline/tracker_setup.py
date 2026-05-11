from src.utils.provenance import ProvenanceMetadataTracker

# Initialize tracker once for the entire pipeline
tracker = ProvenanceMetadataTracker(
    protected_attributes=[
        {'name': 'race', 'type': 'categorical'}, 
        {'name': 'age', 'type': 'continuous'}, 
        {'name': 'marital-status', 'type': 'categorical'}
    ],
    target_variable='income' # Using 'income' as it's the target for the adult dataset
)
