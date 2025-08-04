import pandas as pd
from fredapi import Fred
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

import os
import yaml
from dotenv import load_dotenv



# Load config from config.yml
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yml')
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

DOWNLOAD_NEW_DATA = config.get('DOWNLOAD_NEW_DATA', False)
DATA_DIR = os.path.join(os.path.dirname(__file__), config.get('DATA_DIR', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

# Load environment variables from .env file
load_dotenv()
fred_api_key = os.getenv('FRED_API_KEY')
if not fred_api_key or fred_api_key == 'YOUR_API_KEY_HERE':
    raise ValueError("Please set your FRED_API_KEY in the .env file.")
fred = Fred(api_key=fred_api_key)

# Define the series IDs for M0, M1, and M2
# M0 (Monetary Base) - BOGMBASE
# M1 - M1SL
# M2 - M2SL
series_ids = {
    'M0': 'BOGMBASE',
    'M1': 'M1SL',
    'M2': 'M2SL'
}

# Get all available data (FRED API returns full range if no start_date is given)
end_date = datetime.now()


data = {}
if DOWNLOAD_NEW_DATA:
    for name, series_id in series_ids.items():
        print(f"About to call FRED API for {name} (series ID: {series_id})...")
        # Get all available data by omitting start_date
        series = fred.get_series(series_id, end_date=end_date)
        print(f"Downloaded {name} data from FRED.")
        data[name] = series
        # Save each series as a CSV
        series.to_csv(os.path.join(DATA_DIR, f"{name}.csv"), header=True)
    df = pd.DataFrame(data)
else:
    # Load from CSV files
    for name in series_ids.keys():
        file_path = os.path.join(DATA_DIR, f"{name}.csv")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file {file_path} not found. Set DOWNLOAD_NEW_DATA = True to download.")
        df_csv = pd.read_csv(file_path, index_col=0, parse_dates=True)
        # If the CSV has only one column, convert to Series
        if df_csv.shape[1] == 1:
            series = df_csv.iloc[:, 0]
        else:
            series = df_csv.squeeze(axis=1)
        data[name] = series
    df = pd.DataFrame(data)









# --- Bokeh Interactive Plot ---
from bokeh.plotting import figure, output_file, save, show
from bokeh.models import HoverTool, DatetimeTickFormatter, NumeralTickFormatter, Legend
from bokeh.palettes import Category10
from bokeh.layouts import layout as bokeh_layout

output_file('monetary_supply_interactive_bokeh.html', title='Monetary Supply Measures (M0, M1, M2)')

p = figure(
    title='Monetary Supply Measures (M0, M1, M2)',
    x_axis_type='datetime',
    tools='pan,wheel_zoom,box_zoom,reset,save',
    background_fill_color="white",
    border_fill_color="white",
    sizing_mode='stretch_both'
)

# Ensure all backgrounds and grid lines are white or light
p.outline_line_color = "#cccccc"
p.xgrid.grid_line_color = "#e5e5e5"
p.ygrid.grid_line_color = "#e5e5e5"
p.xgrid.minor_grid_line_color = "#f5f5f5"
p.ygrid.minor_grid_line_color = "#f5f5f5"
p.xgrid.minor_grid_line_alpha = 0.7
p.ygrid.minor_grid_line_alpha = 0.7
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_label_text_color = "#222"
p.yaxis.major_label_text_color = "#222"
p.xaxis.axis_label_text_color = "#222"
p.yaxis.axis_label_text_color = "#222"
p.title.text_color = "#222"
p.legend.background_fill_color = "#fff"
p.legend.border_line_color = "#ccc"

colors = Category10[3]
legend_items = []
for idx, column in enumerate(df.columns):
    line = p.line(df.index, df[column], line_width=2.5, color=colors[idx], legend_label=column)
    legend_items.append((column, [line]))

p.title.text_font_size = '20pt'
p.xaxis.axis_label = 'Date'
p.yaxis.axis_label = 'Billions of Dollars'
p.xaxis.formatter = DatetimeTickFormatter(years='%Y', months='%b %Y')
p.yaxis.formatter = NumeralTickFormatter(format="$0,0")
p.legend.location = 'top_left'
p.legend.label_text_font_size = '13pt'
p.legend.background_fill_alpha = 0.7
p.legend.click_policy = 'hide'
p.grid.grid_line_alpha = 0.4
p.toolbar.logo = None

# Add hover tool
hover = HoverTool(
    tooltips=[
        ("Date", "@x{%F}"),
        ("Value", "@y{$0,0}")
    ],
    formatters={
        '@x': 'datetime',
        '@y': 'numeral'
    },
    mode='vline'
)
p.add_tools(hover)

# Save and show the plot (open in new tab for best full screen experience)
save(p)
show(p)
