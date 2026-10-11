"""Figure 5.5: rank of every proposal with the metamodels against its rank with SWMM.

CLI arguments: base_ranks_csv, adapted_ranks_csv, output_file.
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


def create_plot(base_ranks, adapted_ranks):
    panels = [("Base metamodel", base_ranks), ("Adapted metamodel", adapted_ranks)]
    fig = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        subplot_titles=[title for title, _ in panels],
        horizontal_spacing=0.04,
    )
    for col, (_, ranks) in enumerate(panels, start=1):
        for lvl, color in LEVEL_COLORS.items():
            level_ranks = ranks[ranks["lvl"] == lvl]
            fig.add_trace(
                go.Scatter(
                    x=level_ranks["swmm_rank"],
                    y=level_ranks["metamodel_rank"],
                    mode="markers",
                    marker=dict(color=color, size=6),
                    name=f"{lvl}%",
                    legendgroup=str(lvl),
                    showlegend=col == 1,
                ),
                row=1,
                col=col,
            )
        # Perfect rank agreement
        n_proposals = len(ranks)
        fig.add_trace(
            go.Scatter(
                x=[0, n_proposals],
                y=[0, n_proposals],
                mode="lines",
                line=dict(color="black", dash="dash", width=1.5),
                showlegend=False,
            ),
            row=1,
            col=col,
        )
        fig.update_xaxes(title_text="SWMM rank", row=1, col=col)

    fig.update_yaxes(title_text="Metamodel rank", row=1, col=1)
    fig.update_layout(
        template=custom_template,
        width=1500,
        height=750,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.2),
    )
    fig.update_annotations(font_size=24)  # Subplot titles
    return fig


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base_ranks_csv", type=str)
    parser.add_argument("adapted_ranks_csv", type=str)
    parser.add_argument("output_file", type=str)
    args = parser.parse_args()

    fig = create_plot(
        pd.read_csv(args.base_ranks_csv), pd.read_csv(args.adapted_ranks_csv)
    )
    Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(args.output_file)
