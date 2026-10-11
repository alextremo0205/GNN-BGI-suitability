"""Build the runoff lookup tables (lateral inflows) used to feed the GNN metamodel.

Surrogate hydrological simulations (Chapter 5, Section 5.2.3). The hydrology of a
subcatchment only depends on its own BGIs. Hence, the lateral inflow
of every subcatchment can be pre-computed for each BGI combination with a few SWMM runs,
in which all subcatchments receive the same combination. The metamodel then assembles
the lateral inflows of any BGI configuration from these tables
(see MetamodelSimulator._create_lat_inflows_from_gen).

The lookup tables end at 17:26 (LOOKUP_END_TIME), which is the end of the metamodel
predictions. The SWMM simulations of the workflow run until 18:00, so the last 34 minutes
of SWMM are discarded when comparing both (see calculate_cso_volumes.py).

BGI codes: 1-3 are BGIs in green areas, 4-6 on roofs and 7 on roads. Combinations are
joined with "_" (e.g. "1_4_7"), following lib.network_data. With the baseline (no BGIs),
there are 32 combinations: 4 (green areas) x 4 (roofs) x 2 (roads).

Outputs (in output_dir, by default data/<network>/runoffs_subcatchments_with_BGIs):
- swmm_baseline/lateral_inflow_0.csv
- inps_{single,double,triple}_BGI/input_<code>.inp/.out/.rpt
- inps_{single,double,triple}_BGI/lateral_inflows/lateral_inflow_<code>.csv
"""

import sys
import argparse
from pathlib import Path

import swmmtoolbox.swmmtoolbox as swm
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.paths import NETWORK_FOLDER_PATH
from lib.network_data import (
    BGINetworkDataLoader,
    SINGLE_BGI_CODES,
    DOUBLE_BGI_CODES,
    TRIPLE_BGI_CODES,
)
from lib.translators import BGITranslator
from lib.simulators import PySWMMSimulator

LOOKUP_END_TIME = "17:26:00"


def gen_from_code(code, n_subcatchments):
    """Gene with the BGI combination of code in every subcatchment."""
    gen = torch.zeros(3 * n_subcatchments, dtype=torch.int64)
    for bgi in (int(c) for c in code.split("_")):
        if 1 <= bgi <= 3:  # Green areas
            gen[0::3] = bgi
        elif 4 <= bgi <= 6:  # Roofs
            gen[1::3] = bgi - 3
        elif bgi == 7:  # Roads
            gen[2::3] = 1
        else:
            raise ValueError(f"Unknown BGI code {bgi} in {code}")
    return gen


def extract_lat_inflows(out_file_path, csv_path):
    lateral_inflow_ts = swm.extract(out_file_path, [["node", "", "Lateral_inflow"]])
    lateral_inflow_ts.columns = lateral_inflow_ts.columns.str.replace(
        r"^node_(.*)_Lateral_inflow$", r"\1", regex=True
    )
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    lateral_inflow_ts.to_csv(csv_path)


def set_end_time(lines, end_time):
    return [
        f"END_TIME             {end_time}\n" if line.startswith("END_TIME") else line
        for line in lines
    ]


def simulate_and_extract(simulator, gen, inp_path, csv_path):
    inp_path.parent.mkdir(parents=True, exist_ok=True)
    lines = set_end_time(simulator.translator.gen_to_inp(gen), LOOKUP_END_TIME)
    with open(inp_path, "w") as f:
        f.writelines(lines)
    simulator.simulate(str(inp_path))
    extract_lat_inflows(str(inp_path.with_suffix(".out")), csv_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=NETWORK_FOLDER_PATH / "runoffs_subcatchments_with_BGIs",
    )
    args = parser.parse_args()

    network_data = BGINetworkDataLoader(NETWORK_FOLDER_PATH).load_network_data(
        load_runoff_lookup=False
    )
    simulator = PySWMMSimulator(BGITranslator(network_data))
    n_subcatchments = network_data.n_subcatchments

    baseline_folder = args.output_dir / "swmm_baseline"
    simulate_and_extract(
        simulator,
        torch.zeros(3 * n_subcatchments, dtype=torch.int64),
        baseline_folder / "input.inp",
        baseline_folder / "lateral_inflow_0.csv",
    )

    folders = {
        "inps_single_BGI": SINGLE_BGI_CODES,
        "inps_double_BGI": DOUBLE_BGI_CODES,
        "inps_triple_BGI": TRIPLE_BGI_CODES,
    }
    for folder, codes in folders.items():
        for code in codes:
            print(f"Simulating BGI combination {code}")
            simulate_and_extract(
                simulator,
                gen_from_code(code, n_subcatchments),
                args.output_dir / folder / f"input_{code}.inp",
                args.output_dir
                / folder
                / "lateral_inflows"
                / f"lateral_inflow_{code}.csv",
            )
