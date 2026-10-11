"""Total CSO volume (ML) of one individual, simulated with SWMM and with the metamodel.

The CSO volume is the sum of the volumes spilled over the two weirs of the network.

CLI arguments: swmm_out_file, metamodel_csv_file (flows.csv), lvl, id, out_path.
"""

import argparse

import pandas as pd
import swmmtoolbox.swmmtoolbox as swm
from scipy.integrate import simpson


def m3_to_ML(volume):
    m3_to_litres = 1000
    litres_to_million_litres = 1e-6

    return volume * m3_to_litres * litres_to_million_litres


def get_volume_from_column_ML(series):
    to_seconds = 60  # seconds in a minute
    volume_m3 = simpson(series) * to_seconds
    volume_ML = m3_to_ML(volume_m3)
    return volume_ML


def read_swmm_flows(swmm_out_file):
    flows_swmm = swm.extract(
        swmm_out_file,
        [
            ["link", "weir_30064_40004", "Flow_rate"],
            ["link", "weir_30065_40003", "Flow_rate"],
        ],
    )

    flows_swmm.columns = flows_swmm.columns.str.replace(
        r"^link_", "", regex=True
    ).str.replace(r"(_flow_rate|_Flow_rate)$", "", regex=True)

    # SWMM runs until 18:00 and the metamodel until 17:26 (end of the runoff lookup
    # tables). The last 34 minutes of SWMM are discarded to compare the same period.
    flows_swmm = flows_swmm.iloc[:-34, :].reset_index(drop=True)
    return flows_swmm


def calculate_weir_volume_metrics(swmm_out_file, metamodel_csv_file, lvl, id):
    weir_names = ["weir_30064_40004", "weir_30065_40003"]
    main_weir = "weir_30064_40004"
    secondary_weir = "weir_30065_40003"

    flows_swmm = read_swmm_flows(swmm_out_file)
    flows_metamodel = pd.read_csv(metamodel_csv_file)[weir_names]

    volumes_swmm = flows_swmm.apply(get_volume_from_column_ML)
    volumes_swmm["total_cso"] = volumes_swmm[main_weir] + volumes_swmm[secondary_weir]

    volumes_metamodel = flows_metamodel.apply(get_volume_from_column_ML)
    volumes_metamodel["total_cso"] = (
        volumes_metamodel[main_weir] + volumes_metamodel[secondary_weir]
    )

    volumes_df = pd.DataFrame(
        columns=[
            "lvl",
            "id",
            "total_volume_metamodel",
            "total_volume_swmm",
        ]
    )

    volumes_df.loc[0] = [
        lvl,
        id,
        volumes_metamodel["total_cso"],
        volumes_swmm["total_cso"],
    ]

    return volumes_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("swmm_out_file", type=str)
    parser.add_argument("metamodel_csv_file", type=str)
    parser.add_argument("lvl", type=str)
    parser.add_argument("id", type=str)
    parser.add_argument("out_path", type=str)

    args = parser.parse_args()

    volumes_df = calculate_weir_volume_metrics(
        args.swmm_out_file, args.metamodel_csv_file, args.lvl, args.id
    )
    volumes_df.to_csv(args.out_path, index=False)
