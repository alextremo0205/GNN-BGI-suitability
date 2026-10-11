"""Figure 5.4: total CSO volume of every proposal with SWMM, the base and the adapted metamodel.

CLI arguments: base_volumes_csv, adapted_volumes_csv (aggregated volumes), output_file.
"""

import sys
import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.custom_template_plotly import custom_template
from lib.plotting import LEVEL_COLORS


def create_plot(base_volumes, adapted_volumes):
    panels = [
        ("(a) SWMM Baseline", base_volumes, "total_volume_swmm"),
        ("(b) Base metamodel", base_volumes, "total_volume_metamodel"),
        ("(c) Adapted metamodel", adapted_volumes, "total_volume_metamodel"),
    ]
    fig = make_subplots(
        rows=1,
        cols=3,
        shared_yaxes=True,
        subplot_titles=[title for title, _, _ in panels],
        horizontal_spacing=0.03,
    )
    for col, (_, volumes, column) in enumerate(panels, start=1):
        volumes = volumes.reset_index(drop=True)
        for lvl, color in LEVEL_COLORS.items():
            level_volumes = volumes[volumes["lvl"] == lvl]
            fig.add_trace(
                go.Scatter(
                    x=level_volumes.index,
                    y=level_volumes[column],
                    mode="markers",
                    marker=dict(color=color, size=6),
                    name=f"{lvl}%",
                    legendgroup=str(lvl),
                    showlegend=col == 1,
                ),
                row=1,
                col=col,
            )
        fig.update_xaxes(title_text="ID", row=1, col=col)

    fig.update_yaxes(
        title_text="Total CSO volume [ML]", rangemode="tozero", row=1, col=1
    )
    fig.update_layout(
        template=custom_template,
        width=1800,
        height=700,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.2),
    )
    fig.update_annotations(font_size=24)  # Subplot titles
    return fig


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base_volumes_csv", type=str)
    parser.add_argument("adapted_volumes_csv", type=str)
    parser.add_argument("output_file", type=str)
    args = parser.parse_args()

    fig = create_plot(
        pd.read_csv(args.base_volumes_csv), pd.read_csv(args.adapted_volumes_csv)
    )
    Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(args.output_file)
