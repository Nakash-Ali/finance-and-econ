import os
import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred
from datetime import datetime, timedelta
import yaml

def ingest_fred(series_to_ingest, fred_csv_path, data_dir):
    # Load config for max frequency
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yml')
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    max_freq_mins = int(config.get('DATA_DOWNLOAD_MAX_FREQUENCY_MINS', 0))

    # Load FRED API key
    load_dotenv()
    fred_api_key = os.getenv('FRED_API_KEY')
    if not fred_api_key or fred_api_key == 'YOUR_API_KEY_HERE':
        raise ValueError("Please set your FRED_API_KEY in the .env file.")
    fred = Fred(api_key=fred_api_key)

    # Read FRED series metadata
    fred_meta = pd.read_csv(fred_csv_path)
    fred_meta['series_name'] = fred_meta['series_name'].str.lower()

    # Map original case from series_to_ingest
    ingest_case_map = {s.lower(): s for s in series_to_ingest}

    # Ensure all requested series are present in fred.csv
    for s in series_to_ingest:
        if s.lower() not in fred_meta['series_name'].values:
            raise ValueError(f"Series '{s}' listed in data_to_ingest.csv not found in fred.csv!")

    # Download and save each series
    end_date = datetime.now()
    for _, row in fred_meta.iterrows():
        sname = row['series_name']
        if sname not in ingest_case_map:
            continue
        series_id = row['fred_api_series_id']
        out_name = ingest_case_map[sname]
        out_path = os.path.join(data_dir, f"{out_name}.csv")
        # Check file timestamp logic
        if os.path.exists(out_path) and max_freq_mins > 0:
            mtime = datetime.fromtimestamp(os.path.getmtime(out_path))
            if (end_date - mtime) < timedelta(minutes=max_freq_mins):
                print(f"Skipping download for {out_name}: last updated {mtime}, within {max_freq_mins} mins.")
                continue
        print(f"Downloading {out_name} ({series_id}) from FRED...")
        series = fred.get_series(series_id, end_date=end_date)
        series.to_csv(out_path, header=True)
        print(f"Saved {out_name} to {out_path}")
