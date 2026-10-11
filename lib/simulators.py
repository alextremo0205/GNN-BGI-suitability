"""
Simulators for BGI configurations of the urban drainage network.

* PySWMMSimulator runs the full hydrodynamic model (SWMM) for one BGI configuration.
* MetamodelSimulator prepares the inputs of the GNN metamodel for a population of
  BGI configurations, using pre-computed lateral inflows (runoff lookup tables).

The GNN metamodel itself lives in a separate repository (SWMMMetamodel), whose
location is given by the METAMODEL_CODE_PATH environment variable.

@Author: Alexander Garzón
@e-mail: j.a.garzondiaz@tudelft.nl
"""

import os
import sys
import subprocess
from copy import deepcopy
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import torch
from dotenv import load_dotenv
from torch_geometric.loader import DataLoader

load_dotenv()

METAMODEL_CODE_PATH = os.environ.get("METAMODEL_CODE_PATH")
if METAMODEL_CODE_PATH is None:
    raise EnvironmentError(
        "METAMODEL_CODE_PATH is not set. Point it to your clone of the SWMM GNN "
        "metamodel repository in the .env file (see .env_example)."
    )
sys.path.append(str(Path(METAMODEL_CODE_PATH)))

from SWMMMetamodel.SWMM_Converter import SWMM_Converter
from SWMMMetamodel.SWMM_Simulation import SWMMSimulation


class PySWMMSimulator:
    def __init__(self, translator):
        self.translator = translator

    def simulate(self, inp_path):
        """Run SWMM on an .inp file. The .out and .rpt files are written next to it."""
        try:
            simulation_script = os.path.join(
                os.path.dirname(__file__), "run_single_simulation.py"
            )
            subprocess.run(
                [sys.executable, simulation_script, inp_path],
                check=True,
            )
        except Exception as e:
            print(f"Error in simulation: {e}")

    def simulate_from_gen_in_given_path(self, gen, path):
        """Write the .inp file for a BGI configuration (gen) into path and simulate it."""
        lines = self.translator.gen_to_inp(gen)
        os.makedirs(path, exist_ok=True)
        mod_input_file = os.path.join(path, "input.inp")

        with open(mod_input_file, "w") as f:
            f.writelines(lines)

        self.simulate(mod_input_file)


class MetamodelSimulator:
    def __init__(self, metamodel, normalizer, network_data):
        self.normalizer = normalizer
        self.metamodel = metamodel
        self.metamodel.eval()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.network_data = network_data
        self.pre_trained_weights_name = ""

    def set_pre_trained_weights_name(self, name):
        self.pre_trained_weights_name = name

    def get_pre_trained_weights_name(self):
        return self.pre_trained_weights_name

    def get_batch_from_population(self, population):
        """Build the normalized PyG batch (one graph per individual) for the metamodel."""
        lat_inflows = self._get_lat_inflows_from_hash_table(population)
        return self._get_batch_changing_inflow(population, lat_inflows)

    def _get_batch_changing_inflow(self, gen, lat_inflows):
        number_of_individuals = len(gen)
        set_of_windows = []
        for i, lat_inflow in enumerate(lat_inflows):
            win = self._get_simulation_as_window(
                self.network_data.inp_path,
                lat_inflow,
                steps_behind=9,
                name_simulation=f"Simulation_{i}",
            ).to(self.device)
            win = self.normalizer.normalize_window_eval(win)
            win = _remove_unnecessary_information_of_normalized_window(win)
            set_of_windows.append(win)

        dataloader = DataLoader(
            set_of_windows,
            batch_size=number_of_individuals,
            shuffle=False,
        )
        batch = next(iter(dataloader))
        return batch

    def _generate_heads_as_zero_depth(
        self, index_lat_inflow, nodes_elevation, steps_behind
    ):
        nodes_list = list(nodes_elevation.keys())
        nodes_elevation_values = list(nodes_elevation.values())
        nodes_elevation_values_np = np.array(nodes_elevation_values)
        elevation_matrix_nodes = np.tile(
            nodes_elevation_values_np, (steps_behind, 1)
        )  # Assumes the initial condition is 0 water depth everywhere
        synt_heads_raw_data = pd.DataFrame(
            elevation_matrix_nodes,
            index=index_lat_inflow[:steps_behind],
            columns=nodes_list,
        )
        return synt_heads_raw_data

    def _generate_flowrate_as_zeros(self, index_lat_inflow, edges_list, steps_behind):
        zeros_matrix_edges = np.zeros(
            (steps_behind, len(edges_list))
        )  # Assumes the initial condition is 0 flow rate everywhere
        synt_flows_raw_data = pd.DataFrame(
            zeros_matrix_edges,
            index=index_lat_inflow[:steps_behind],
            columns=edges_list,
        )
        return synt_flows_raw_data

    def _get_simulation_as_window(
        self, inp_path, lat_inflow_raw_data, steps_behind, name_simulation
    ):
        converter = SWMM_Converter(inp_path, is_directed=True)
        G = converter.inp_to_G()

        nodes_elevation = nx.get_node_attributes(G, "elevation")
        nodes_list = list(nodes_elevation.keys())

        nodes_subcatchment = nx.get_node_attributes(G, "subcatchment")
        reversed_nodes_subcatchment = {
            value: key for key, value in nodes_subcatchment.items()
        }

        lat_inflow_raw_data = lat_inflow_raw_data.rename(
            columns=reversed_nodes_subcatchment
        )
        missing_nodes = set(nodes_list) - set(lat_inflow_raw_data.columns)

        for i in missing_nodes:
            lat_inflow_raw_data[i] = 0

        # Pad the beginning of the event with zeros (dry initial conditions)
        zeros_df = pd.DataFrame(
            0, index=range(steps_behind), columns=lat_inflow_raw_data.columns
        )
        lat_inflow_raw_data = pd.concat(
            [zeros_df, lat_inflow_raw_data], ignore_index=True
        )

        index_lat_inflow = lat_inflow_raw_data.index
        edges_list = list(nx.get_edge_attributes(G, "name_conduits").values())

        heads_raw_data = self._generate_heads_as_zero_depth(
            index_lat_inflow, nodes_elevation, steps_behind
        )
        flowrate_raw_data = self._generate_flowrate_as_zeros(
            index_lat_inflow, edges_list, steps_behind
        )

        raw_data = {
            "heads_raw_data": heads_raw_data,
            "flowrate_raw_data": flowrate_raw_data,
            "lateral_inflow_raw_data": lat_inflow_raw_data,
        }
        sim = SWMMSimulation(G, raw_data, name_simulation)
        win = sim.get_simulation_in_one_window(steps_behind, include_target_data=False)

        return win

    def _create_lat_inflows_from_gen(self, gen):
        ids = self.network_data.subcatchment_ids
        prototype_lat_inflows = deepcopy(self.network_data.baseline_lat_inflows)

        for ind_subcatchment in range(len(ids)):
            sub_gen = gen[ind_subcatchment * 3 : ind_subcatchment * 3 + 3]
            code = self._get_id_code_from_sub_gen(sub_gen)

            if code == "":
                continue

            name_subcatchment = ids[ind_subcatchment][5:]
            # TODO Fix this, as it is hardcoded for Loenen
            if name_subcatchment == "40001":
                name_subcatchment = "40002"
            lat_inflows_with_BGIs = self.network_data.hash_table_inflows[code][
                name_subcatchment
            ]
            prototype_lat_inflows[name_subcatchment] = lat_inflows_with_BGIs
        return prototype_lat_inflows

    def _get_id_code_from_sub_gen(self, sub_gen):
        first_component = sub_gen[0].item()
        second_component = sub_gen[1].item() + 3 if sub_gen[1].item() > 0 else 0
        third_component = 7 if sub_gen[2].item() > 0 else 0
        code = ""
        if first_component != 0:
            code += str(first_component) + "_"
        if second_component != 0:
            code += str(second_component) + "_"
        if third_component != 0:
            code += str(third_component)
        if code.endswith("_"):
            code = code[:-1]
        return code

    def _get_lat_inflows_from_hash_table(self, batch):
        all_lat_inflows = []
        for gen in batch:
            lat_inflows = self._create_lat_inflows_from_gen(gen)
            all_lat_inflows.append(lat_inflows)
        return all_lat_inflows


def _remove_unnecessary_information_of_normalized_window(win):
    win.conduit_phonebook = None
    win.length = None
    win.lateral_inflow = None
    win.geom_1 = None
    win.ground_level = None
    win.geom_2 = None
    win.h_x = None
    win.aprox_conduit_volume = None
    win.max_depth = None
    win.pos = None
    win.in_offset = None
    win.norm_aprox_conduit_volume = None
    win.q_x = None
    win.slope = None
    win.out_offset = None
    win.roughness = None
    win.subcatchment = None
    win.conduit_shape = None
    return win
