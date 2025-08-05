import os
import pandas as pd
import yaml

def get_data_dir_from_config(config_path=None):
    """
    Reads the data directory from the config.yml file.
    Returns the path as a string.
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    data_dir = config.get('data_dir', 'data')
    # Make path absolute relative to project root
    if not os.path.isabs(data_dir):
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), data_dir)
    return data_dir

def convert_series_to_delta(series_name):
    """
    Convert a series to its period-over-period delta (difference).
    Args:
        series_name (str): The name of the series (e.g., 'm2')
    Saves:
        {series_name}_delta_derived.csv in the data_dir
    """
    data_dir = get_data_dir_from_config()
    series_path = os.path.join(data_dir, f"{series_name}.csv")
    if not os.path.exists(series_path):
        raise FileNotFoundError(f"Series file not found: {series_path}")
    series = pd.read_csv(series_path, index_col=0, parse_dates=True)
    # Compute delta (difference)
    delta = series.squeeze().diff()
    df_delta = pd.DataFrame({f'{series_name}_delta_derived': delta})
    out_path = os.path.join(data_dir, f"{series_name}_delta_derived.csv")
    df_delta.to_csv(out_path)
    print(f"Saved delta series to {out_path}")

# Entrypoint
if __name__ == "__main__":
    convert_series_to_delta('nfp')
