"""Extract one variable from a SWMM .out file into a CSV file.

Used to build the dataset of SWMM simulations that fine-tunes the metamodel
(Chapter 5, Section 5.2.3): 100 simulations, 20 per intervention level, split into
training (10), validation (5) and testing (5) simulations per level.

CLI arguments: out_file, variable (a key of VARIABLES), variable_output (CSV path).
"""

import argparse

import swmmtoolbox.swmmtoolbox as swm

VARIABLES = {
    "hydraulic_head": [["node", "", "Hydraulic_head"]],
    "total_inflow": [["node", "", "Total_inflow"]],
    "flooding_flow": [["node", "", "Flow_lost_flooding"]],
    "lateral_inflow": [["node", "", "Lateral_inflow"]],
    "runoff": [["subcatchment", "", "Runoff_rate"]],
    "flow_rate": [["link", "", "Flow_rate"]],
    "velocity": [["link", "", "Flow_velocity"]],
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("out_file", type=str)
    parser.add_argument("variable", type=str, choices=VARIABLES)
    parser.add_argument("variable_output", type=str)
    args = parser.parse_args()

    out_timeseries = swm.extract(args.out_file, VARIABLES[args.variable])
    out_timeseries.to_csv(args.variable_output)
