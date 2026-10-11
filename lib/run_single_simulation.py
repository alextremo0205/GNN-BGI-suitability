"""Run a SWMM simulation for one .inp file. Called in a subprocess by PySWMMSimulator."""

import sys

from pyswmm import Simulation

if len(sys.argv) != 2:
    print("Usage: python run_single_simulation.py <path_to_inp_file>")
    sys.exit(1)

inp_path = sys.argv[1]

with Simulation(inp_path) as sim:
    for step in sim:
        pass  # Complete the simulation
