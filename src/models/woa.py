import numpy as np
import math
import random

class MetadataWOAAuditor:
    def __init__(self, metadata_logs, privileged_group_key, num_whales=10, max_iter=50):
        """
        Initializes the WOA Auditor.
        :param metadata_logs: A list of dictionaries representing the JSONB logs from the pipeline.
        :param privileged_group_key: The demographic group used as the baseline for DI and SPD.
        :param num_whales: Population size of search agents.
        :param max_iter: Maximum number of search iterations.
        """
        self.metadata_logs = metadata_logs
        self.privileged_group = privileged_group_key
        self.num_whales = num_whales
        self.max_iter = max_iter
        
        # Search space boundaries: [0 to number of logs - 1]
        self.dim = 1 # Searching across pipeline stages (1D search space)
        self.lb = 0
        self.ub = len(metadata_logs) - 1
        
        # Track the Best Whale (Highest Bias)
        self.best_position = np.zeros(self.dim)
        self.best_fitness = float('-inf') # We are MAXIMIZING bias for the audit

    def calculate_fitness(self, log_index, target_group_key):
        """
        The Fitness Function: f(X) = |SPD| + |1 - DI|
        Calculates how 'biased' a specific pipeline stage is.
        """
        # 1. Discretize the continuous position to an integer index
        idx = int(np.round(np.clip(log_index, self.lb, self.ub)))
        snapshot = self.metadata_logs[idx]["intersectional_demographics"]
        
        # 2. Extract Data
        priv_data = snapshot.get(self.privileged_group, {'total_count': 1, 'total_approve': 1})
        target_data = snapshot.get(target_group_key, {'total_count': 1, 'total_approve': 1})
        
        # 3. Calculate Selection Rates (Probability of positive outcome)
        # Added a small epsilon (1e-5) to prevent division by zero errors
        rate_priv = target_data['total_approve'] / (target_data['total_count'] + 1e-5)
        rate_target = priv_data['total_approve'] / (priv_data['total_count'] + 1e-5)
        
        # 4. Calculate Metrics
        spd = abs(rate_target - rate_priv)
        di = rate_target / (rate_priv + 1e-5)
        
        # 5. Thesis Fitness Formula
        fitness_score = spd + abs(1 - di)
        
        return fitness_score

    def run_audit(self, target_group_key):
        """
        Executes the main WOA Scouting loop.
        """
        # Initialize whale population randomly across the search space (log indexes)
        whales_pos = np.random.uniform(self.lb, self.ub, (self.num_whales, self.dim))
        
        for t in range(self.max_iter):
            # Evaluate fitness for all whales
            for i in range(self.num_whales):
                # Ensure boundary limits
                whales_pos[i] = np.clip(whales_pos[i], self.lb, self.ub)
                
                # Calculate bias fitness
                fitness = self.calculate_fitness(whales_pos[i][0], target_group_key)
                
                # Update the Global Best (Highest Bias Found)
                if fitness > self.best_fitness:
                    self.best_fitness = fitness
                    self.best_position = whales_pos[i].copy()
            
            # Update WOA Parameters (a decreases linearly from 2 to 0)
            a = 2.0 - (t * (2.0 / self.max_iter))
            
            # Update positions of whales
            for i in range(self.num_whales):
                r1 = random.random()
                r2 = random.random()
                
                A = 2 * a * r1 - a
                C = 2 * r2
                
                l = random.uniform(-1, 1)
                p = random.random()
                
                # Equation variables based on thesis flowchart
                if p < 0.5:
                    if abs(A) < 1:
                        # Shrinking Encircling Mechanism (Exploitation)
                        D = abs(C * self.best_position - whales_pos[i])
                        whales_pos[i] = self.best_position - A * D
                    else:
                        # Search for Prey (Exploration)
                        random_whale_idx = math.floor(self.num_whales * random.random())
                        random_whale = whales_pos[random_whale_idx]
                        D = abs(C * random_whale - whales_pos[i])
                        whales_pos[i] = random_whale - A * D
                else:
                    # Spiral Bubble-Net Attack (Exploitation)
                    D_prime = abs(self.best_position - whales_pos[i])
                    b = 1  # logarithmic spiral shape constant
                    whales_pos[i] = D_prime * math.exp(b * l) * math.cos(2 * math.pi * l) + self.best_position

        # Return the discrete index of the highest-bias pipeline stage
        best_log_index = int(np.round(self.best_position[0]))
        return {
            "highest_bias_stage_index": best_log_index,
            "max_fitness_score": self.best_fitness,
            "transformation_name": self.metadata_logs[best_log_index]["transformation_name"]
        }


# Simulated JSONB Database logs
mock_jsonb_logs = [
    {
        "transformation_name": "RAW_DATA",
        "intersectional_demographics": {
            "race:White|sex:Male|age:40-60": {"total_count": 1000, "total_approve": 500},
            "race:Black|sex:Female|age:20-40": {"total_count": 300, "total_approve": 120}
        }
    },
    {
        "transformation_name": "CLEAN_NULLS_AGE",
        "intersectional_demographics": {
            "race:White|sex:Male|age:40-60": {"total_count": 1000, "total_approve": 500},
            "race:Black|sex:Female|age:20-40": {"total_count": 300, "total_approve": 40} # Bias introduced here!
        }
    }
]

# Initialize Auditor
auditor = MetadataWOAAuditor(
    metadata_logs=mock_jsonb_logs,
    privileged_group_key="race:White|sex:Male|age:40-60",
    num_whales=5,
    max_iter=20
)

# Run the hunt
result = auditor.run_audit(target_group_key="race:Black|sex:Female|age:20-40")
print(f"Audit Complete! Bias Hotspot Found:\n{result}")