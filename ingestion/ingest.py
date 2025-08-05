import os
import sys
import pandas as pd
import importlib

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_TO_INGEST_PATH = os.path.join(BASE_DIR, 'data_to_ingest.csv')
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')

# Read config
import yaml
CONFIG_PATH = os.path.join(os.path.dirname(BASE_DIR), 'config.yml')
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)
DOWNLOAD_NEW_DATA = config.get('DOWNLOAD_NEW_DATA', False)

if not DOWNLOAD_NEW_DATA:
    print("DOWNLOAD_NEW_DATA is False. Skipping ingestion.")
    sys.exit(0)

# Read data_to_ingest.csv
inputs = pd.read_csv(DATA_TO_INGEST_PATH)
inputs['series_name'] = inputs['series_name'].str.lower()

# Group by source
for source, group in inputs.groupby('source'):
    source_dir = os.path.join(BASE_DIR, source)
    source_csv = os.path.join(source_dir, f'{source}.csv')
    source_py = os.path.join(source_dir, f'{source}.py')
    if not os.path.exists(source_csv):
        raise FileNotFoundError(f"Source CSV not found: {source_csv}")
    if not os.path.exists(source_py):
        raise FileNotFoundError(f"Source ingestion script not found: {source_py}")
    # Import the ingestion function dynamically
    spec = importlib.util.spec_from_file_location(f"{source}_ingest", source_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ingest_func = getattr(mod, f"ingest_{source}")
    # Call the ingestion function with the list of series to ingest
    ingest_func(group['series_name'].tolist(), source_csv, DATA_DIR)
