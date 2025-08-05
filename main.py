import os
import subprocess
import sys

# --- Run ingestion before processing and plotting ---
subprocess.run([sys.executable, os.path.join('ingestion', 'ingest.py')], check=True)

# --- Run processing (convert nominal to real series, etc.) ---
subprocess.run([sys.executable, os.path.join('processing', 'convert_series_to_real.py')], check=True)
subprocess.run([sys.executable, os.path.join('processing', 'convert_series_to_delta.py')], check=True)

# --- Run plotting ---
subprocess.run([sys.executable, os.path.join('plotting', 'plot.py')], check=True)
