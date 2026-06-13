import json
with open('data/provenance_metadata.json', encoding='utf-8') as f:
    data = json.load(f)
for step in data:
    total_fav = sum(group['favorable_outcomes'] for group in step['intersectional_demographics'].values())
    total_unfav = sum(group['unfavorable_outcomes'] for group in step['intersectional_demographics'].values())
    print(step['transformation_name'], 'Fav=', total_fav, 'Unfav=', total_unfav)
