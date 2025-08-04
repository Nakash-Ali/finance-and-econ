
# --- Refactored for Reusability: Measures, Data Loading, and Plotting ---
import pandas as pd
from fredapi import Fred
import matplotlib.pyplot as plt
from datetime import datetime
import os
import yaml
from dotenv import load_dotenv

# --- Config and Environment ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yml')
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

DOWNLOAD_NEW_DATA = config.get('DOWNLOAD_NEW_DATA', False)
DATA_DIR = os.path.join(os.path.dirname(__file__), config.get('DATA_DIR', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

load_dotenv()
fred_api_key = os.getenv('FRED_API_KEY')
if not fred_api_key or fred_api_key == 'YOUR_API_KEY_HERE':
    raise ValueError("Please set your FRED_API_KEY in the .env file.")
fred = Fred(api_key=fred_api_key)

# --- Measure Abstraction ---
class Measure:
    def __init__(self, name, series_ids, title=None, y_axis_label=None):
        self.name = name
        self.series_ids = series_ids  # dict: {label: FRED series id}
        self.title = title or name
        self.y_axis_label = y_axis_label or 'Value'
        self.df = None

    def load_data(self, download_new=DOWNLOAD_NEW_DATA, data_dir=DATA_DIR, fred=fred):
        data = {}
        if download_new:
            end_date = datetime.now()
            for label, series_id in self.series_ids.items():
                print(f"Downloading {label} ({series_id}) from FRED...")
                series = fred.get_series(series_id, end_date=end_date)
                data[label] = series
                series.to_csv(os.path.join(data_dir, f"{label}.csv"), header=True)
            self.df = pd.DataFrame(data)
        else:
            for label in self.series_ids.keys():
                file_path = os.path.join(data_dir, f"{label}.csv")
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Data file {file_path} not found. Set DOWNLOAD_NEW_DATA = True to download.")
                df_csv = pd.read_csv(file_path, index_col=0, parse_dates=True)
                if df_csv.shape[1] == 1:
                    series = df_csv.iloc[:, 0]
                else:
                    series = df_csv.squeeze(axis=1)
                data[label] = series
            self.df = pd.DataFrame(data)
        return self.df

    def analyze(self):
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        print(f"Analysis for measure: {self.name}")
        print(self.df.describe())
        print("\nLatest values:")
        print(self.df.tail())

    def plot_bokeh(self, output_html=None):
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        from bokeh.plotting import figure, output_file, save, show
        from bokeh.models import HoverTool, DatetimeTickFormatter, NumeralTickFormatter
        from bokeh.palettes import Category10

        output_html = output_html or f"{self.name}_interactive_bokeh.html"
        output_file(output_html, title=self.title)

        p = figure(
            title=self.title,
            x_axis_type='datetime',
            tools='pan,wheel_zoom,box_zoom,reset,save',
            background_fill_color="white",
            border_fill_color="white",
            sizing_mode='stretch_both'
        )

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

        colors = Category10[max(3, len(self.df.columns))]
        for idx, column in enumerate(self.df.columns):
            p.line(self.df.index, self.df[column], line_width=2.5, color=colors[idx % len(colors)], legend_label=column)

        p.title.text_font_size = '20pt'
        p.xaxis.axis_label = 'Date'
        p.yaxis.axis_label = self.y_axis_label
        p.xaxis.formatter = DatetimeTickFormatter(years='%Y', months='%b %Y')
        p.yaxis.formatter = NumeralTickFormatter(format="$0,0")
        p.legend.location = 'top_left'
        p.legend.label_text_font_size = '13pt'
        p.legend.background_fill_alpha = 0.7
        p.legend.click_policy = 'hide'
        p.grid.grid_line_alpha = 0.4
        p.toolbar.logo = None

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

        save(p)
        show(p)

# --- Example Usage: Monetary Supply Measure ---
monetary_supply_measure = Measure(
    name="monetary_supply",
    series_ids={
        'M0': 'BOGMBASE',
        'M1': 'M1SL',
        'M2': 'M2SL'
    },
    title='Monetary Supply Measures (M0, M1, M2)',
    y_axis_label='Billions of Dollars'
)

# Load data for the measure
monetary_supply_measure.load_data()

# Analyze the measure (prints summary and latest values)
monetary_supply_measure.analyze()

# Plot the measure (Bokeh interactive chart)
monetary_supply_measure.plot_bokeh()
