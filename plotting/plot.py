import os
import pandas as pd
import ast

class Measure_Plot:
    def __init__(self, name, series_names, title=None, y_axis_label=None):
        self.name = name
        self.series_names = series_names
        self.title = title or name
        self.y_axis_label = y_axis_label or 'Value'
        self.df = None

    def load_data(self, data_dir):
        data = {}
        for sname in self.series_names:
            csv_path = os.path.join(data_dir, f"{sname}.csv")
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"Data file {csv_path} not found. Run ingestion first.")
            df_csv = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            if df_csv.shape[1] == 1:
                series = df_csv.iloc[:, 0]
            else:
                series = df_csv.squeeze(axis=1)
            data[sname] = series
        self.df = pd.DataFrame(data)
        return self.df

    def analyze(self):
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        print(f"Analysis for measure: {self.name}")
        print(self.df.describe())
        print("\nLatest values:")
        print(self.df.tail())

    def plot_bokeh(self, output_html=None, outputs_dir=None):
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        from bokeh.plotting import figure, output_file, save, show
        from bokeh.models import HoverTool, DatetimeTickFormatter, NumeralTickFormatter
        from bokeh.palettes import Category10

        # Set outputs_dir to 'outputs' folder in project root if not provided
        if outputs_dir is None:
            outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
        os.makedirs(outputs_dir, exist_ok=True)
        # Use all series names joined by _ as the filename
        if output_html is None:
            base_name = '_'.join(self.series_names)
            output_html = f"{base_name}_interactive_bokeh.html"
        output_html_path = os.path.join(outputs_dir, output_html)
        output_file(output_html_path, title=self.title)

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
        print(f"Bokeh plot saved to: {output_html_path}")
        show(p)

# Entrypoint for plotting
if __name__ == "__main__":
    import yaml
    # Read config for data dir
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yml')
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), config.get('DATA_DIR', 'data'))
    #os.makedirs(DATA_DIR, exist_ok=True)

    # Read plotting config
    measures_df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'measure_plotting.csv'))
    for _, row in measures_df.iterrows():
        # Only plot if is_active is 'Y'
        if str(row.get('is_active', '')).strip().upper() != 'Y':
            continue
        if not isinstance(row['series_names'], str) or not row['series_names'].strip():
            continue
        series_names = [s.strip() for s in row['series_names'].split('|') if s.strip()]
        title = row['title']
        y_axis_label = row['y_axis_label']
        # Use the joined series names as the plot name
        name = '_'.join(series_names)
        measure = Measure_Plot(name, series_names, title, y_axis_label)
        measure.load_data(DATA_DIR)
        #measure.analyze()
        measure.plot_bokeh(outputs_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs'))
