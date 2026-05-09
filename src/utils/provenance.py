import pandas as pd
import datetime
import functools

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
        :param target_variable: String name of the binary outcome column.
                                Example: 'loan_approval'
        """
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
                # Replace string placeholders
                df_meta[col] = df_meta[col].replace(missing_vals, "Unknown")
                # Fill actual NaN/None
                df_meta[col] = df_meta[col].fillna("Unknown")
                # Convert back to string if it was mixed
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
                    # Ensure we ignore "Unknown" values while binning
                    is_unknown = df_meta[col] == "Unknown"
                    numeric_series = pd.to_numeric(df_meta.loc[~is_unknown, col], errors='coerce')
                    
                    # Group into discrete ranges
                    binned_series = pd.cut(numeric_series, bins=5).astype(str)
                    df_meta.loc[~is_unknown, col] = binned_series
                    
                    # Clean up any 'nan' resulting from unparseable values mapped to NaN by to_numeric
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
        
        # Cross-tabulation / Group by all protected attributes
        groups = df_meta.groupby(attrs)
        
        intersectional_demographics = {}
        for name, group in groups:
            # Flatten the multi-index name into an intersectional group string
            if isinstance(name, tuple):
                group_key = "|".join([f"{k}:{v}" for k, v in zip(attrs, name)])
            else:
                group_key = f"{attrs[0]}:{name}"
                
            total_count = len(group)
            
            favorable = 0
            if self.target_variable in df.columns:
                target_series = group[self.target_variable]
                # Filter for favorable outcomes (target_variable == 1)
                favorable = int(((target_series == 1) | (target_series == '1') | (target_series == 1.0) | (target_series == True)).sum())
                
            selection_rate = favorable / total_count if total_count > 0 else 0.0
            
            intersectional_demographics[group_key] = {
                "total_count": total_count,
                "favorable_outcomes": favorable,
                "selection_rate": selection_rate
            }
            
        return intersectional_demographics

    def track(self, transformation_name=None):
        """
        Decorator for tracking a data transformation function.
        Validates ethical constraints and logs the transformation snapshot.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Attempt to find the input DataFrame from arguments
                input_df = None
                if args and isinstance(args[0], pd.DataFrame):
                    input_df = args[0]
                elif kwargs:
                    for val in kwargs.values():
                        if isinstance(val, pd.DataFrame):
                            input_df = val
                            break
                            
                # Ethical Constraint Check BEFORE processing
                if input_df is not None and self.target_variable in input_df.columns:
                    unique_targets = input_df[self.target_variable].dropna().unique()
                    if len(unique_targets) > 2:
                        error_msg = f"Fairness metrics (SPD/DI) require a binary target. Target variable '{self.target_variable}' contains more than 2 unique values."
                        print(f"Ethical Constraint Error: {error_msg}")
                        raise ValueError(error_msg)

                # Execute the transformation function
                result_df = func(*args, **kwargs)
                
                # Identify the output DataFrame
                df_to_analyze = None
                if isinstance(result_df, pd.DataFrame):
                    df_to_analyze = result_df
                elif input_df is not None:
                    # In case the function modified df in-place and didn't return it
                    df_to_analyze = input_df
                
                # Package results into a single JSON object
                if df_to_analyze is not None:
                    snapshot = self._generate_snapshot(df_to_analyze)
                    
                    metadata_record = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "transformation_name": transformation_name or func.__name__,
                        "intersectional_demographics": snapshot
                    }
                    
                    self._handle_metadata(metadata_record)
                    
                return result_df
            return wrapper
        return decorator

    def _handle_metadata(self, record):
        """
        Stores metadata as a JSON object internally.
        NOTE: Kept local until signal is given to export to PostgreSQL JSONB.
        """
        self.metadata_records.append(record)
        print(f"Generated Provenance Metadata for: {record['transformation_name']}")
