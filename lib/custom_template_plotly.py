import plotly.graph_objects as go
import plotly.express as px

WIDTH = 1080
HEIGHT = 810
font_size = 24
marker_size = 16

custom_template = {
    "layout": go.Layout(
        font={
            "family": "Times New Roman",  # Use only allowed font
            "size": font_size,
            "color": "#333333",  # Slightly darker for better readability
        },
        title={
            "font": {
                "family": "Times New Roman",  # Consistent with artwork font rules
                "size": font_size,
                "color": "#000000",
            },
            "x": 0.5,  # Center the title
            "xanchor": "center",
        },
        xaxis={
            "title": {
                "font": {
                    "family": "Times New Roman",
                    "size": font_size,
                    "color": "#333333",
                },
            },
            "tickfont": {
                "family": "Times New Roman",
                "size": font_size,
            },
            "showspikes": True,
            "spikemode": "across",
            "spikesnap": "cursor",
            "showline": True,
            "linewidth": 1,
            "linecolor": "#444",
            "mirror": True,
            "showgrid": True,
            "gridcolor": "#e6e6e6",
            "ticks": "outside",
            "tickcolor": "#444",
            "title_standoff": 15,  # <- use this instead of putting it under 'title'
            "automargin": True,  # <- this is required for standoff to work
        },
        yaxis={
            "title": {
                "font": {
                    "family": "Times New Roman",
                    "size": font_size,
                    "color": "#333333",
                },
            },
            "tickfont": {
                "family": "Times New Roman",
                "size": font_size,
            },
            "showline": True,
            "linewidth": 1,
            "linecolor": "#444",
            "mirror": True,
            "showgrid": True,
            "gridcolor": "#e6e6e6",
            "ticks": "outside",
            "tickcolor": "#444",
            "title_standoff": 15,  # <- use this instead of putting it under 'title'
            "automargin": True,  # <- this is required for standoff to work
        },
        legend={
            "font": {
                "family": "Times New Roman",  # Use Times New Roman for legend text
                "size": font_size * 0.9,  # Slightly smaller than axis labels
                "color": "#333333",
            },
            "bordercolor": "#e6e6e6",
            "borderwidth": 1,
        },
        hovermode="x",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin={"l": 80, "r": 40, "t": 60, "b": 60},
        colorway=px.colors.qualitative.G10,  # Good balance of contrast and clarity
        width=1200,  # Set width
        height=800,  # Set height
    )
}
