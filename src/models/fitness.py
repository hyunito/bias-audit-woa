def calculate_bias_fitness(snapshot, privileged_group_key, target_group_key):
    """
    The Fitness Function: f(X) = |SPD| + |1 - DI|
    Calculates how 'biased' a specific pipeline stage is.
    
    :param snapshot: The intersectional_demographics dictionary for a single log.
    :param privileged_group_key: The string key for the baseline group.
    :param target_group_key: The string key for the target unprivileged group.
    :return: A float representing the bias fitness score.
    """
  
    priv_data = snapshot.get(privileged_group_key, {})
    target_data = snapshot.get(target_group_key, {})
    
    if 'selection_rate' in priv_data:
        rate_priv = priv_data['selection_rate']
    else:
        count_priv = priv_data.get('total_count', 1)
        approve_priv = priv_data.get('total_approve', 1)
        rate_priv = approve_priv / (count_priv + 1e-5)
        
    if 'selection_rate' in target_data:
        rate_target = target_data['selection_rate']
    else:
        count_target = target_data.get('total_count', 1)
        approve_target = target_data.get('total_approve', 1)
        rate_target = approve_target / (count_target + 1e-5)
 
    spd = abs(rate_target - rate_priv)
    di = rate_target / (rate_priv + 1e-5)
    
    fitness_score = spd + abs(1 - di)
    
    return fitness_score
