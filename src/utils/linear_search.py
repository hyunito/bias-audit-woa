from pandas._libs.tslibs import timestamps
import json
import os
import time
import psutil
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "ground_truth.txt")  
file_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "provenance_metadata.json")

def find_ground_truth_max_fitness():
    
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        stages = json.load(f)
        
    
    for i, stage in enumerate(stages):
        script_name = stage.get("script_name", "Unknown")
        trans_name = stage.get("transformation_name", "Unknown")
        demos = stage.get("intersectional_demographics", {})
        
        # Get/Compute privileged rate
        rate_priv = stage.get("highest_selection_rate")
        privileged_group_key = stage.get("privileged_group")
        
        # Fallback to compute privileged group if not stored
        if rate_priv is None or privileged_group_key is None:
            highest_rate = -1.0
            for g_key, g_metrics in demos.items():
                if g_metrics.get("total_count", 0) >= 30:
                    curr_rate = g_metrics.get("selection_rate_favorable_outcomes", 0.0)
                    if curr_rate > highest_rate:
                        highest_rate = curr_rate
                        privileged_group_key = g_key
            rate_priv = highest_rate
            
        if rate_priv is None or rate_priv <= 0:
            rate_priv = 1.0
            
        max_score = float("-inf")
        best_demo = "None"
        
        # Linear search (brute-force scan) over all demographic groups in this stage
        for demo_key, metrics in demos.items():
            total_count = metrics.get("total_count", 0)
            
            # Enforce the same constraint: ignore groups with count < 30
            if total_count < 30:
                continue
                
            rate_target = metrics.get("selection_rate_favorable_outcomes")
            if rate_target is None:
                rate_target = metrics.get("selection_rate", 0.0)
                
            # Compute fitness metrics
            spd = abs(rate_target - rate_priv)
            di = rate_target / (rate_priv + 1e-5)
            fitness_score = spd + abs(1 - di)
            
            if fitness_score > max_score:
                max_score = fitness_score
                best_demo = demo_key
              
        if max_score != float("-inf"):
            result = {
                "max_fitness_score": max_score,
                "script_name": script_name,
                "transformation_name": trans_name,
                "demographic_group": best_demo
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{result}\n")
        else:
            entry =f"{{'max_fitness_score': 0.0, 'script_name': '{script_name}', 'transformation_name': '{trans_name}', 'demographic_group': 'No groups >= 30 samples'}}"
            
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(entry)
def get_peak_memory():
    """
    Returns the peak working set memory usage of the process on Windows in bytes.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    if hasattr(mem_info, 'peak_wset'):
        return mem_info.peak_wset
    return mem_info.rss

    


if __name__ == "__main__":
    t_start = time.perf_counter()
    find_ground_truth_max_fitness()
    t_end = time.perf_counter()
    latency = t_end - t_start
    peak_mem = get_peak_memory() / (1024 * 1024)
