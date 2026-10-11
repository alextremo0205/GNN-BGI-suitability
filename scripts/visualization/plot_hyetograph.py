"""Plot the hyetograph of the design rainfall event (composite storm, 2085, T = 2 years)."""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.paths import NETWORK_FOLDER_PATH, RESULTS_FOLDER_PATH
from lib.custom_template_plotly import custom_template

RAINFALL_PATH = NETWORK_FOLDER_PATH / "Composite_rainfall_2085_2_years.csv"


def read_data(path):
    return pd.read_csv(path)


def create_plot(df, output_file):
    fig = go.Figure()

    # Filter data until 10:20
    df_filtered = df[df["Time"] <= "10:20"]

    fig.add_trace(
        go.Bar(
            x=df_filtered["Time"],  # Time
            y=df_filtered["Value"],  # Rainfall intensity
            marker=dict(
                color="#00aeef",  # Softer blue fill
                line=dict(
                    color="#088abb", width=1.5  # Border color  # Border thickness
                ),
            ),
        )
    )

    fig.update_layout(
        title="",  # No title
        showlegend=False,  # Hide legend
        xaxis_title="Time",
        yaxis_title="Intensity (mm/h)",
        template=custom_template,  # Or your custom template
        width=1200,
        height=800,
        xaxis=dict(
            tickmode="auto",  # Let Plotly auto-select ticks
            nticks=10,  # Reduce number of ticks
        ),
        bargap=0,
    )

    fig.write_image(output_file)

    return fig


if __name__ == "__main__":
    output_file = RESULTS_FOLDER_PATH / "figures" / "hyetograph_2085.pdf"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    create_plot(read_data(RAINFALL_PATH), output_file)
