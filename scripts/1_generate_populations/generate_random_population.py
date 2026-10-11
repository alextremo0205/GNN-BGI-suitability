"""Generate one random BGI population file for a chosen intervention level.

In a single execution, it creates one population for one intervention level
(percentage of genes with a BGI) and saves it as CSV.

The script:
1. Loads BGI network data to determine the number of genes.
2. Creates a base population of zeros (no BGIs in place).
3. Mutates each individual at the requested intervention level.
4. Saves the mutated population to the output CSV path.

CLI arguments:
- population_size (int): Number of individuals to generate.
- intervention_level (int): Percentage of genes to mutate per individual.
- output_path (str): Destination CSV file path.
- --seed (int, optional): Seed of the random number generator.

Mutation encoding:
- Mutated gene values are sampled as integers in [1, 3].
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
from lib.network_data import create_bgi_network_loader


def mutate(X, k, min_val, max_val):
    """
    X: (n, m) tensor
    k: number of entries to modify per row
    min_val, max_val: inclusive integer range for new values
    """
    n, m = X.shape
    assert k <= m, "k must be <= number of columns"

    # Clone to avoid in-place modification
    X_new = X.clone()

    # Random column indices per row
    col_idx = torch.rand(n, m).argsort(dim=1)[:, :k]

    # Row indices
    row_idx = torch.arange(n).unsqueeze(1)

    # Random integer values
    random_values = torch.randint(
        min_val, max_val + 1, (n, k), device=X.device, dtype=torch.int
    )

    # Apply modifications
    X_new[row_idx, col_idx] = random_values

    return X_new


def get_number_of_mutations(intervention_level, number_of_genes):
    """Number of genes with a BGI for an intervention level given in percent."""
    return int(np.ceil(intervention_level / 100 * number_of_genes).item())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("population_size", type=int)
    parser.add_argument("intervention_level", type=int)  # e.g. "10", "20"
    parser.add_argument("output_path", type=str)  # full output file path
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        torch.manual_seed(args.seed)

    network_data = create_bgi_network_loader(NETWORK_FOLDER_PATH).load_network_data(
        load_runoff_lookup=False
    )

    number_of_genes = 3 * network_data.n_subcatchments
    number_of_mutations = get_number_of_mutations(
        args.intervention_level, number_of_genes
    )

    # This assumes that the original system has no BGIs in place
    gen = torch.zeros((1, number_of_genes), dtype=torch.int)
    population = torch.tile(gen, (args.population_size, 1))

    mutated_population = mutate(population, k=number_of_mutations, min_val=1, max_val=3)

    np.savetxt(
        args.output_path,
        mutated_population.numpy(),
        delimiter=",",
        fmt="%.6f",
    )
