import numpy as np
import math
import random
import time
import psutil
import os
import re
from fitness import calculate_bias_fitness, calculate_3d_fitness, load_provenance_data

class MetadataWOAAuditor:
    def __init__(self, metadata_logs=None, num_whales=10, max_iter=50):
        """
        Initializes the WOA Auditor with a 3D search space.
        :param metadata_logs: Optional list of dictionaries representing the JSONB logs.
                              If None, will fetch from PostgreSQL database.
        :param num_whales: Population size of search agents.
        :param max_iter: Maximum number of search iterations.
        """
        self.num_whales = num_whales
        self.max_iter = max_iter
        
        # Load search space structure
        if metadata_logs is not None:
            # Parse mock logs into the fitness module structure
            import fitness
            fitness._scripts = []
            fitness._transformations = {}
            fitness._demographics = {}
            fitness._raw_records = {}
            
            for log in metadata_logs:
                script = log.get("script_name", "mock_script.py")
                trans = log.get("transformation_name", "mock_trans")
                
                if script not in fitness._scripts:
                    fitness._scripts.append(script)
                    fitness._transformations[script] = []
                if trans not in fitness._transformations[script]:
                    fitness._transformations[script].append(trans)
                
                fitness._raw_records[(script, trans)] = log
                demos = log.get("intersectional_demographics", {})
                fitness._demographics[(script, trans)] = sorted(list(demos.keys()))
                
            self.scripts, self.transformations, self.demographics = fitness._scripts, fitness._transformations, fitness._demographics
            fitness._logs_cache = True # Prevent reloading database when mock is used
        else:
            from fitness import get_space_dimensions
            self.scripts, self.transformations, self.demographics = get_space_dimensions()
            
        self.dim = 3
        self.best_position = np.zeros(self.dim)
        self.best_fitness = float('-inf')

    def clip_position(self, pos):
        """
        Clips a 3D position [s, t, d] to the valid uneven bounds of the search space.
        """
        if not self.scripts:
            return np.zeros(self.dim)
            
        s = int(round(np.clip(pos[0], 0, len(self.scripts) - 1)))
        script_name = self.scripts[s]
        
        t_max = len(self.transformations.get(script_name, [])) - 1
        t_max = max(0, t_max)
        t = int(round(np.clip(pos[1], 0, t_max)))
        
        trans_list = self.transformations.get(script_name, [])
        trans_name = trans_list[t] if trans_list else "None"
        
        d_max = len(self.demographics.get((script_name, trans_name), [])) - 1
        d_max = max(0, d_max)
        d = int(round(np.clip(pos[2], 0, d_max)))
        
        return np.array([float(s), float(t), float(d)])

    def calculate_fitness(self, pos):
        """
        Calls calculate_3d_fitness using s_idx, t_idx, d_idx coordinates.
        """
        fitness, _, _, _ = calculate_3d_fitness(pos[0], pos[1], pos[2])
        return fitness

    def run_audit(self):
        """
        Executes the main WOA Scouting loop over the uneven 3D search space.
        """
        if not self.scripts:
            print("No search space found. Verify database or fallback JSON path.")
            return {
                "max_fitness_score": 0.0,
                "script_name": "None",
                "transformation_name": "None",
                "demographic_group": "None"
            }
            
        # Initialize whales inside valid uneven boundaries
        whales_pos = []
        for _ in range(self.num_whales):
            s_val = random.randint(0, len(self.scripts) - 1)
            script_name = self.scripts[s_val]
            
            t_max = len(self.transformations.get(script_name, [])) - 1
            t_max = max(0, t_max)
            t_val = random.randint(0, t_max)
            trans_list = self.transformations.get(script_name, [])
            trans_name = trans_list[t_val] if trans_list else "None"
            
            d_max = len(self.demographics.get((script_name, trans_name), [])) - 1
            d_max = max(0, d_max)
            d_val = random.randint(0, d_max)
            
            whales_pos.append([float(s_val), float(t_val), float(d_val)])
            
        whales_pos = np.array(whales_pos)
        
        self.best_fitness = float('-inf')
        self.best_position = whales_pos[0].copy()
        
        for t in range(self.max_iter):
            # Evaluate fitness for all whales
            for i in range(self.num_whales):
                whales_pos[i] = self.clip_position(whales_pos[i])
                fitness = self.calculate_fitness(whales_pos[i])
                
                # We want to maximize the bias fitness score (higher score = more biased stage/demographic)
                if fitness > self.best_fitness:
                    self.best_fitness = fitness
                    self.best_position = whales_pos[i].copy()
            
            a = 2.0 - (t * (2.0 / self.max_iter)) # Linearly decreases from 2 to 0
            
            for i in range(self.num_whales):
                r1 = random.random()
                r2 = random.random()
                
                A = 2 * a * r1 - a
                C = 2 * r2
                
                l = random.uniform(-1, 1)
                p = random.random()
                
                if p < 0.5:
                    if abs(A) < 1:
                        # Encircling prey
                        D = abs(C * self.best_position - whales_pos[i])
                        new_pos = self.best_position - A * D
                    else:
                        # Search for prey (random search agent selection)
                        random_whale_idx = random.randint(0, self.num_whales - 1)
                        random_whale = whales_pos[random_whale_idx]
                        D = abs(C * random_whale - whales_pos[i])
                        new_pos = random_whale - A * D
                else:
                    # Spiral bubble-net attack
                    D_prime = abs(self.best_position - whales_pos[i])
                    b = 1 
                    new_pos = D_prime * math.exp(b * l) * math.cos(2 * math.pi * l) + self.best_position
                
                whales_pos[i] = self.clip_position(new_pos)

        # Get final names and values from the best position found
        best_fitness, best_script, best_trans, best_demo = calculate_3d_fitness(
            self.best_position[0], self.best_position[1], self.best_position[2]
        )
        
        return {
            "max_fitness_score": best_fitness,
            "script_name": best_script,
            "transformation_name": best_trans,
            "demographic_group": best_demo
        }

def get_peak_memory():
    """
    Returns the peak working set memory usage of the process on Windows,
    or falls back to max RSS on Unix/macOS, in bytes.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    if hasattr(mem_info, 'peak_wset'):
        return mem_info.peak_wset
    return mem_info.rss

def log_audit_run(result, latency, peak_memory):
    """
    Appends the run metrics to data/woa_performance_logs.txt in a chronological manner.
    """
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "woa_performance_logs.txt")
    
    # Determine the next run number by scanning the log file
    run_num = 1
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
                runs = re.findall(r"Run (\d+) Status:", content)
                if runs:
                    run_num = max(int(r) for r in runs) + 1
        except Exception:
            pass
            
    peak_mem_mb = peak_memory / (1024 * 1024)
    
    log_entry = (
        f"Run {run_num} Status:\n"
        f"Algorithms Latency: {latency:.6f} seconds\n"
        f"Peak Memory Usage: {peak_mem_mb:.2f} MB\n"
        f"Bias: {result}\n\n"
    )
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)
        
    print(f"Metrics successfully logged to: {os.path.abspath(log_path)}")

if __name__ == "__main__":
    print("=== Running Standalone WOA on Real Logs (DB/JSON) ===")
    import fitness
    fitness._logs_cache = None # Force cache reset to load real data
    
    # Start latency and memory tracking
    t_start = time.perf_counter()
    
    auditor_real = MetadataWOAAuditor(
        metadata_logs=None,
        num_whales=10,
        max_iter=30
    )
    result_real = auditor_real.run_audit()
    
    t_end = time.perf_counter()
    latency = t_end - t_start
    peak_mem = get_peak_memory()
    
    print(f"Audit Complete! Standalone WOA Bias Hotspot Found:\n{result_real}")
    print(f"Algorithms Latency: {latency:.6f} seconds")
    print(f"Peak Memory Usage: {peak_mem / (1024 * 1024):.2f} MB")
    
    # Log run output to performance logs
    log_audit_run(result_real, latency, peak_mem)
