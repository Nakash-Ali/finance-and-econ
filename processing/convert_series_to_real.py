
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

def convert_series_to_real(series_name):
    """
    Convert a nominal series to real values using the CPI series.
    Args:
        series_name (str): The name of the nominal series (e.g., 'm2')
    Saves:
        {series_name}_real_derived.csv in the data_dir
    """
    data_dir = get_data_dir_from_config()
    nominal_path = os.path.join(data_dir, f"{series_name}.csv")
    cpi_path = os.path.join(data_dir, "cpi.csv")
    if not os.path.exists(nominal_path):
        raise FileNotFoundError(f"Nominal series file not found: {nominal_path}")
    if not os.path.exists(cpi_path):
        raise FileNotFoundError(f"CPI series file not found: {cpi_path}")
    nominal = pd.read_csv(nominal_path, index_col=0, parse_dates=True)
    cpi = pd.read_csv(cpi_path, index_col=0, parse_dates=True)
    # Align on index (date)
    df = pd.DataFrame({series_name: nominal.squeeze(), 'cpi': cpi.squeeze()})
    # Convert to real: real = nominal * (cpi_base / cpi)
    # Use 1982-1984 average CPI as the base (CPI-U, base period = 100)
    # Find the average CPI for 1982-01-01 to 1984-12-31
    cpi_base_period = df.loc[(df.index >= '1982-01-01') & (df.index <= '1984-12-31'), 'cpi']
    if cpi_base_period.empty:
        raise ValueError("No CPI data found for 1982-1984 base period. Cannot convert to constant dollars.")
    cpi_base = cpi_base_period.mean()
    df[f'{series_name}_real_derived'] = df[series_name] * (cpi_base / df['cpi'])
    # Save only the real series
    out_path = os.path.join(data_dir, f"{series_name}_real_derived.csv")
    df[[f'{series_name}_real_derived']].to_csv(out_path)
    print(f"Saved real series (1982-1984 dollars) to {out_path}")
    
    
# Entrypoint
if __name__ == "__main__":
  convert_series_to_real('m0')
  convert_series_to_real('m1')
  convert_series_to_real('m2')
  