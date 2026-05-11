from src.utils.provenance import ProvenanceMetadataTracker

tracker = ProvenanceMetadataTracker(
    protected_attributes=[
        {'name': 'race', 'type': 'categorical'}, 
        {'name': 'age', 'type': 'continuous'}, 
        {'name': 'marital-status', 'type': 'categorical'}
    ],
    target_variable={'name': 'income', 'positive': '>50K', 'negative': '<=50K'}
)
