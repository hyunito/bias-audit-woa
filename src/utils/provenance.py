import pandas as pd
import datetime
import functools
import json
import os
class ProvenanceMetadataTracker:
    """
    A wrapper class for data transformations that generates summary statistics 
    for an auditing system and tracks intersectional metadata.
    """
    def __init__(self, protected_attributes, target_variable):
        """
        Initializes the tracker with configuration requirements.
        
        :param protected_attributes: List of dicts defining metadata schema.
                                     Example: [{'name': 'race', 'type': 'categorical'}, 
                                               {'name': 'age', 'type': 'continuous'}]
        :param target_variable: Dict containing target column details or a string name.
                                Example: {'name': 'income', 'positive': '>50K', 'negative': '<=50K'}
        """
        valid_types = {'categorical', 'continuous'}
        for attr in protected_attributes:
            attr_type = attr.get('type')
            if attr_type not in valid_types:
                raise ValueError(
                    f"Invalid type '{attr_type}' for protected attribute '{attr.get('name', 'Unknown')}'. "
                    f"Type must be either 'categorical' or 'continuous'."
                )

        self.protected_attributes = protected_attributes
        self.target_variable = target_variable
        self.metadata_records = []

    def _standardize_missing(self, df, columns):
        """
        Standardizes missing values to 'Unknown'.
        Targets NaN, null, empty strings "", and "?".
        """
        df_meta = df.copy()
        missing_vals = ["", "?", "nan", "NaN", "Null", "null"]
        
        for col in columns:
            if col in df_meta.columns:
                df_meta[col] = df_meta[col].replace(missing_vals, "Unknown")
                df_meta[col] = df_meta[col].astype(object)
                df_meta[col] = df_meta[col].astype(str)
        return df_meta

    def _bin_continuous(self, df_meta):
        """
        Bins continuous variables into 5 discrete ranges using pandas.cut.
        """
        for attr in self.protected_attributes:
            if attr.get('type') == 'continuous':
                col = attr['name']
                if col in df_meta.columns:
               
                    is_unknown = df_meta[col] == "Unknown"
                    numeric_series = pd.to_numeric(df_meta.loc[~is_unknown, col], errors='coerce')
                    
                    binned_series = pd.qcut(numeric_series, q=5, duplicates='drop')
                    df_meta.loc[~is_unknown, col] = binned_series
                    
                    df_meta[col] = df_meta[col].replace(["nan", "NaN"], "Unknown")
        return df_meta

    def _generate_snapshot(self, df):
        """
        Generates the intersectional snapshot with counts and rates.
        Produces a flattened dictionary with keys like 'race:Asian|sex:Female|age:21-40'.
        """
        attrs = [attr['name'] for attr in self.protected_attributes if attr['name'] in df.columns]
        if not attrs:
            return {}

        df_meta = self._standardize_missing(df, attrs)
        df_meta = self._bin_continuous(df_meta)
        
        groups = df_meta.groupby(attrs)
        
        intersectional_demographics = {}
        for name, group in groups:
            
            if isinstance(name, tuple):
                group_key = "|".join([f"{k}:{v}" for k, v in zip(attrs, name)])
            else:
                group_key = f"{attrs[0]}:{name}"
                
            total_count = len(group)
            
            favorable = 0
            unfavorable = 0
            
            target_col = self.target_variable.get('name') if isinstance(self.target_variable, dict) else self.target_variable
            
            if target_col in df.columns:
                target_series = group[target_col]
                
                if isinstance(self.target_variable, dict):
                    pos_val = self.target_variable.get('positive')
                    neg_val = self.target_variable.get('negative')
                    favorable = int((target_series == pos_val).sum())
                    unfavorable = int((target_series == neg_val).sum())
                else:
                    
                    favorable = int(((target_series == 1) | (target_series == '1') | (target_series == 1.0) | (target_series == True)).sum())
                    unfavorable = int(((target_series == 0) | (target_series == '0') | (target_series == 0.0) | (target_series == False)).sum())
                
            valid_outcomes = favorable + unfavorable
            selection_rate_favorable_outcomes = favorable / total_count
            selection_rate_unfavorable_outcomes = unfavorable / total_count
            
            intersectional_demographics[group_key] = {
                "total_count": total_count,
                "favorable_outcomes": favorable,
                "unfavorable_outcomes": unfavorable,
                "selection_rate_favorable_outcomes": selection_rate_favorable_outcomes,
                "selection_rate_unfavorable_outcomes": selection_rate_unfavorable_outcomes
            }
            
        return intersectional_demographics

    def _calculate_bias_metrics(self, snapshot):
        """
        Calculates Statistical Parity Difference and Disparate Impact
        for each intersectional demographic group compared to the highest performing group.
        """
        rates = [group_data.get('selection_rate_favorable_outcomes', 0.0) 
                 for group_data in snapshot.values()]
        
        if not rates:
            return
            
        max_rate = max(rates)
        
        for group_data in snapshot.values():
            rate = group_data.get('selection_rate_favorable_outcomes', 0.0)
            spd = max_rate - rate
            di = rate / max_rate if max_rate > 0 else 1.0
            
            group_data['bias_metrics'] = {
                "statistical_parity_difference": round(spd, 4),
                "disparate_impact": round(di, 4)
            }

    def track(self, transformation_name=None):
        """
        Decorator for tracking a data transformation function.
        Validates ethical constraints and logs the transformation snapshot.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                
                input_df = None
                if args and isinstance(args[0], pd.DataFrame):
                    input_df = args[0]
                elif kwargs:
                    for val in kwargs.values():
                        if isinstance(val, pd.DataFrame):
                            input_df = val
                            break
                            
                row_count_before = len(input_df) if input_df is not None else None

                target_col = self.target_variable.get('name') if isinstance(self.target_variable, dict) else self.target_variable
                if input_df is not None and target_col in input_df.columns:
                    unique_targets = input_df[target_col].dropna().unique()
                    
                    unique_targets = [val for val in unique_targets if val != "Unknown"]
                    if len(unique_targets) > 2:
                        error_msg = f"Fairness metrics (SPD/DI) require a binary target. Target variable '{target_col}' contains more than 2 unique values (excluding 'Unknown')."
                        print(f"Ethical Constraint Error: {error_msg}")
                        raise ValueError(error_msg)

                result_df = func(*args, **kwargs)
                
                df_to_analyze = None
                if isinstance(result_df, pd.DataFrame):
                    df_to_analyze = result_df
                elif input_df is not None:
                    
                    df_to_analyze = input_df
                
                if df_to_analyze is not None:
                    snapshot = self._generate_snapshot(df_to_analyze)
                    row_count_after = len(df_to_analyze)
                    
                    self._calculate_bias_metrics(snapshot)
                    
                    metadata_record = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "transformation_name": transformation_name or func.__name__,
                        "row_count_before": row_count_before,
                        "row_count_after": row_count_after,
                        "intersectional_demographics": snapshot
                    }
                    
                    self._handle_metadata(metadata_record)
                    
                return result_df
            return wrapper
        return decorator

    def _handle_metadata(self, record):
        """
        Stores metadata as a JSON object internally.
        """
        self.metadata_records.append(record)
        print(f"Generated Provenance Metadata for: {record['transformation_name']}")

    def export_to_json(self, filepath="provenance_metadata.json"):
        """
        Exports the tracked metadata records to a JSON file.
        """
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(filepath, 'w') as f:
            json.dump(self.metadata_records, f, indent=4)
        print(f"Successfully exported {len(self.metadata_records)} provenance records to {filepath}")
