"""Run one SWMM simulation for a selected BGI population individual.

It loads one population matrix from CSV, selects a single individual by index, writes
its .inp file into the output directory and runs SWMM there (input.inp/.out/.rpt).

CLI arguments:
- population_csv (str): Path to the CSV file containing a population matrix.
- inx_population (int): Row index of the individual to simulate.
- output_directory (str): Directory where simulation outputs are written.
"""

import sys
import argparse
from pathlib import Path

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.paths import NETWORK_FOLDER_PATH
from lib.translators import BGITranslator
from lib.network_data import create_bgi_network_loader
from lib.simulators import PySWMMSimulator

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("population_csv", type=str)
    parser.add_argument("inx_population", type=int)
    parser.add_argument("output_directory", type=str)
    args = parser.parse_args()

    network_data = create_bgi_network_loader(NETWORK_FOLDER_PATH).load_network_data(
        load_runoff_lookup=False
    )
    pyswmm_simulator = PySWMMSimulator(BGITranslator(network_data))

    population_np = np.loadtxt(args.population_csv, delimiter=",")
    population = torch.tensor(population_np, dtype=torch.int64)

    gen = population[args.inx_population]
    pyswmm_simulator.simulate_from_gen_in_given_path(gen, args.output_directory)
