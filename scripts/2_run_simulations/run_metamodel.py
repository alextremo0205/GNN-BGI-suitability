"""Run the GNN metamodel for a whole BGI population.

It loads a pre-trained GNN metamodel, builds its inputs for every individual of the
population (using the runoff lookup tables) and predicts the hydraulic heads and flows.

Outputs, one folder per individual:
- <output_dir>/id_XX/heads.csv
- <output_dir>/id_XX/flows.csv

CLI arguments:
- input_csv (str): Path to the CSV file containing a population matrix.
- metamodel_name (str): Key of METAMODELS.
- output_dir (str): Folder where the per-individual folders are written.
"""

import sys
import argparse
import platform
from pathlib import Path

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.paths import (
    NETWORK_FOLDER_PATH,
    METAMODEL_FILES_PATH,
    SAVED_OBJECTS_FOLDER_PATH,
)
from lib.network_data import create_bgi_network_loader
from lib.simulators import MetamodelSimulator
from lib.utils import load_pickle, load_yaml

# Importable once lib.simulators has added METAMODEL_CODE_PATH to sys.path
from SWMMMetamodel.models.Model_main import ModelFactory

# Weights and hyperparameters of each metamodel, in data/<network>/metamodel_files
METAMODELS = {
    # Best metamodel of Chapter 4, used as-is
    "baseline_metamodel": {
        "weights": "baseline_metamodel.pt",
        "config": "metamodel_config.yaml",
    },
    # Baseline metamodel with a weir decoder, followed by fine-tuning of all weights
    "adapted_metamodel": {
        "weights": "adapted_metamodel.pt",
        "config": "metamodel_config_weirs.yaml",
    },
}
NORMALIZER_PATH = (
    SAVED_OBJECTS_FOLDER_PATH / "saved_normalizers" / "normalizer_Loenen_v7.pkl"
)
NUM_CONDUITS, NUM_NODES = 708, 342


def _setup_device():
    """Set up the device for computation."""
    if platform.system() == "Darwin" and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_metamodel(device, metamodel_name):
    """Load the pre-trained metamodel."""
    metamodel_files = METAMODELS[metamodel_name]
    hyperparameters = load_yaml(METAMODEL_FILES_PATH / metamodel_files["config"])
    metamodel = ModelFactory(hyperparameters["model_name"])(**hyperparameters).to(
        device
    )

    path_to_metamodel_weights = METAMODEL_FILES_PATH / metamodel_files["weights"]

    pre_trained_weights = torch.load(
        path_to_metamodel_weights,
        map_location=device,
        weights_only=True,
    )
    metamodel.load_state_dict(pre_trained_weights, strict=True)

    print("Using pre_trained_weights:", path_to_metamodel_weights)
    return metamodel


def process_population_file(metamodel_simulator, input_csv_file, output_dir, device):
    """Simulate a population file and save the heads and flows of each individual."""
    population_np = np.loadtxt(input_csv_file, delimiter=",")
    population = torch.tensor(population_np, dtype=torch.int64)
    batch = metamodel_simulator.get_batch_from_population(population).to(device)

    with torch.inference_mode(), torch.amp.autocast(device.type):
        norm_heads_from_metamodel, norm_flows_from_metamodel = (
            metamodel_simulator.metamodel(batch)
        )

    for id in range(len(batch.ptr) - 1):
        start_nodes = batch.ptr[id]
        end_nodes = batch.ptr[id + 1]

        start_flows = (start_nodes * NUM_CONDUITS / NUM_NODES).to(torch.int64)
        end_flows = (end_nodes * NUM_CONDUITS / NUM_NODES).to(torch.int64)

        df_flows = metamodel_simulator.normalizer.get_unscaled_flows_pd(
            norm_flows_from_metamodel[start_flows:end_flows]
        )
        df_heads = metamodel_simulator.normalizer.get_unnormalized_heads_pd(
            norm_heads_from_metamodel[start_nodes:end_nodes]
        )

        current_folder = Path(output_dir) / f"id_{id:02d}"
        current_folder.mkdir(parents=True, exist_ok=True)

        df_heads.to_csv(current_folder / "heads.csv", index=False)
        df_flows.to_csv(current_folder / "flows.csv", index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", type=str)
    parser.add_argument("metamodel_name", type=str, choices=METAMODELS)
    parser.add_argument("output_dir", type=str)
    args = parser.parse_args()

    device = _setup_device()
    network_data = create_bgi_network_loader(NETWORK_FOLDER_PATH).load_network_data()
    normalizer = load_pickle(NORMALIZER_PATH)
    metamodel = load_metamodel(device, args.metamodel_name)

    metamodel_simulator = MetamodelSimulator(
        metamodel=metamodel,
        normalizer=normalizer,
        network_data=network_data,
    )
    metamodel_simulator.set_pre_trained_weights_name(args.metamodel_name)

    process_population_file(
        metamodel_simulator, args.input_csv, args.output_dir, device
    )


if __name__ == "__main__":
    main()
