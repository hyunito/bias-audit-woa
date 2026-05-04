import datetime
import functools
import json

DEFAULT_JSONDB_FILE = 'provenance.json'

class ProvenanceTracker:
    """
    A class to track data transformations and operations for provenance.
    Logs each operation with timestamp and details.
    """
    def __init__(self):
        self.logs = []

    def log_operation(self, operation_type, details, timestamp=None):
        """
        Log an operation.

        :param operation_type: str, e.g., 'age_cleaning', 'remove_duplicates'
        :param details: dict, details like {'rows_before': 100, 'rows_after': 95, 'description': 'removed invalid ages'}
        :param timestamp: str or datetime, optional, defaults to now
        """
        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        elif isinstance(timestamp, datetime.datetime):
            timestamp = timestamp.isoformat()

        log_entry = {
            'timestamp': timestamp,
            'operation': operation_type,
            'details': details
        }
    def log_row_change(self, operation_type, row_index, column, old_value, new_value, timestamp=None):
        """
        Log a specific row-level change.

        :param operation_type: str, e.g., 'sex_cleaning'
        :param row_index: int, the DataFrame index of the changed row
        :param column: str, the column name that changed
        :param old_value: any, the original value
        :param new_value: any, the new value
        :param timestamp: str or datetime, optional
        """
        # Convert pandas/numpy types to JSON-serializable Python types
        def to_serializable(val):
            if hasattr(val, 'item'):  # numpy scalar
                return val.item()
            elif isinstance(val, (int, float, str, bool, type(None))):
                return val
            else:
                return str(val)  # fallback to string

        old_value = to_serializable(old_value)
        new_value = to_serializable(new_value)

        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        elif isinstance(timestamp, datetime.datetime):
            timestamp = timestamp.isoformat()

        log_entry = {
            'timestamp': timestamp,
            'operation': operation_type,
            'details': {
                'row_index': row_index,
                'column': column,
                'old_value': old_value,
                'new_value': new_value
            }
        }
        self.logs.append(log_entry)
        print(f"Row change logged: {operation_type} on row {row_index}, {column}: {old_value} -> {new_value}")

    def track(self, operation_type=None, include_args=False):
        """
        Return a decorator that logs provenance for the wrapped function.

        Example:
            @tracker.track('clean_age', include_args=True)
            def clean_age(df):
                ...
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = datetime.datetime.now()
                result = func(*args, **kwargs)
                duration = (datetime.datetime.now() - start_time).total_seconds()

                details = {
                    'function': func.__name__,
                    'result_type': type(result).__name__,
                    'duration_seconds': duration,
                }

                if include_args:
                    details['args'] = repr(args)
                    details['kwargs'] = repr(kwargs)

                if args and hasattr(args[0], '__len__'):
                    try:
                        details['rows_before'] = len(args[0])
                    except Exception:
                        pass

                if hasattr(result, '__len__'):
                    try:
                        details['rows_after'] = len(result)
                    except Exception:
                        pass

                self.log_operation(operation_type or func.__name__, details)
                return result

            return wrapper

        return decorator

    def get_logs(self):
        """Return the list of all logged operations."""
        return self.logs

    def save_logs(self, filepath=DEFAULT_JSONDB_FILE):
        """
        Save logs to a JSON file, appending to existing logs if the file exists.

        This simulates appending to a JSONDB backend, preserving history across runs.
        """
        # Load existing logs if file exists
        existing_logs = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is corrupted, start fresh
            existing_logs = []
            print(f"Warning: Could not load existing {filepath}. Starting with empty logs.")
        
        # Append current logs
        all_logs = existing_logs + self.logs
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(all_logs, f, indent=4)
        print(f"Logs saved to {filepath} (appended {len(self.logs)} new entries)")

    def load_logs(self, filepath=DEFAULT_JSONDB_FILE):
        """
        Load logs from a JSON file.

        This simulates reading from a JSONDB backend by restoring the
        in-memory provenance log list from file.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.logs = json.load(f)
            print(f"Logs loaded from {filepath}")
        except FileNotFoundError:
            print(f"No provenance file found at {filepath}. Starting with empty logs.")
            self.logs = []

    def clear_logs(self):
        """Clear all logs."""
        self.logs = []

# Global instance for easy access across modules
tracker = ProvenanceTracker()


def track_provenance(operation_type=None, include_args=False):
    """Convenience decorator using the global tracker."""
    return tracker.track(operation_type, include_args)
