import psycopg2
import os
import numpy as np
from dotenv import load_dotenv
import json

# Cache for the loaded logs hierarchy
_logs_cache = None
_scripts = []
_transformations = {} # script_name -> list of trans_names
_demographics = {}    # (script_name, trans_name) -> list of demo_keys
_raw_records = {}     # (script_name, trans_name) -> log_data dict

def load_provenance_data():
    global _logs_cache, _scripts, _transformations, _demographics, _raw_records
    if _logs_cache is not None:
        return
    
    load_dotenv()
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    
    rows = []
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        cursor.execute("SELECT log_data FROM provenance_logs ORDER BY id ASC")
        for r in cursor.fetchall():
            val = r[0]
            if isinstance(val, str):
                rows.append(json.loads(val))
            else:
                rows.append(val)
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database connection failed, falling back to JSON: {e}")
        
    if not rows:
        # Try local JSON files as fallbacks
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "provenance_metadata.json"),
            os.path.join(os.path.dirname(__file__), "provenance_metadata.json"),
            "data/provenance_metadata.json",
            "provenance_metadata.json"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        rows = json.load(f)
                    print(f"Successfully loaded fallback JSON from {path}")
                    break
                except Exception as json_err:
                    pass
                
    # Build hierarchy from rows
    _scripts = []
    _transformations = {}
    _demographics = {}
    _raw_records = {}
    
    for log_data in rows:
        script = log_data.get("script_name")
        trans = log_data.get("transformation_name")
        
        if not script or not trans:
            continue
            
        if script not in _scripts:
            _scripts.append(script)
            _transformations[script] = []
            
        if trans not in _transformations[script]:
            _transformations[script].append(trans)
            
        _raw_records[(script, trans)] = log_data
        
        demos = log_data.get("intersectional_demographics", {})
        valid_demos = [k for k, v in demos.items() if v.get("total_count", 0) >= 30]
        _demographics[(script, trans)] = sorted(valid_demos)
        
    _logs_cache = True

def get_space_dimensions():
    load_provenance_data()
    return _scripts, _transformations, _demographics

def calculate_3d_fitness(s_idx, t_idx, d_idx):
    load_provenance_data()
    
    if not _scripts:
        return 0.0, "None", "None", "None"
        
    # 1. Map s_idx to script
    s_val = int(round(np.clip(s_idx, 0, len(_scripts) - 1)))
    script_name = _scripts[s_val]
    
    # 2. Map t_idx to transformation within script
    trans_list = _transformations.get(script_name, [])
    if not trans_list:
        return 0.0, script_name, "None", "None"
    t_val = int(round(np.clip(t_idx, 0, len(trans_list) - 1)))
    trans_name = trans_list[t_val]
    
    # 3. Map d_idx to demographic key within transformation
    demo_list = _demographics.get((script_name, trans_name), [])
    if not demo_list:
        return 0.0, script_name, trans_name, "None"
    d_val = int(round(np.clip(d_idx, 0, len(demo_list) - 1)))
    demo_key = demo_list[d_val]
    
    # Fetch raw record and check total_count
    log_data = _raw_records[(script_name, trans_name)]
    target_data = log_data.get("intersectional_demographics", {}).get(demo_key, {})
    
    total_count = target_data.get("total_count", 0)
    # Ignore if total_count < 30
    if total_count < 30:
        return -999.0, script_name, trans_name, demo_key
        
    # Get privileged information
    rate_priv = log_data.get("highest_selection_rate")
    privileged_group_key = log_data.get("privileged_group")
    
    # Fallback to compute privileged group if not stored
    if rate_priv is None or privileged_group_key is None:
        highest_rate = -1.0
        for g_key, g_metrics in log_data.get("intersectional_demographics", {}).items():
            if g_metrics.get("total_count", 0) >= 30:
                curr_rate = g_metrics.get("selection_rate_favorable_outcomes", 0.0)
                if curr_rate > highest_rate:
                    highest_rate = curr_rate
                    privileged_group_key = g_key
        rate_priv = highest_rate
        
    if rate_priv is None or rate_priv <= 0:
        rate_priv = 1.0
        
    rate_target = target_data.get("selection_rate_favorable_outcomes")
    if rate_target is None:
        rate_target = target_data.get("selection_rate", 0.0)
        
    # Calculate SPD and DI
    spd = abs(rate_target - rate_priv)
    di = rate_target / (rate_priv + 1e-5)
    
    # Fitness Function: f(X) = |SPD| + |1 - DI|
    fitness_score = spd + abs(1 - di)
    
    return fitness_score, script_name, trans_name, demo_key

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
    
    if 'selection_rate_favorable_outcomes' in priv_data:
        rate_priv = priv_data['selection_rate_favorable_outcomes']
    elif 'selection_rate' in priv_data:
        rate_priv = priv_data['selection_rate']
    else:
        count_priv = priv_data.get('total_count', 1)
        approve_priv = priv_data.get('total_approve', 1)
        rate_priv = approve_priv / (count_priv + 1e-5)
        
    if 'selection_rate_favorable_outcomes' in target_data:
        rate_target = target_data['selection_rate_favorable_outcomes']
    elif 'selection_rate' in target_data:
        rate_target = target_data['selection_rate']
    else:
        count_target = target_data.get('total_count', 1)
        approve_target = target_data.get('total_approve', 1)
        rate_target = approve_target / (count_target + 1e-5)
 
    spd = abs(rate_target - rate_priv)
    di = rate_target / (rate_priv + 1e-5)
    
    fitness_score = spd + abs(1 - di)
    
    return fitness_score
