import torch

from generate_random_population import get_number_of_mutations, mutate


def test_number_of_mutations_is_rounded_up():
    assert get_number_of_mutations(1, 150) == 2
    assert get_number_of_mutations(50, 150) == 75


def test_each_individual_has_exactly_k_bgis_with_valid_values():
    population = torch.zeros((20, 30), dtype=torch.int)

    mutated = mutate(population, k=7, min_val=1, max_val=3)

    assert torch.all((mutated != 0).sum(dim=1) == 7)
    assert torch.all(mutated[mutated != 0] >= 1)
    assert torch.all(mutated <= 3)
    assert torch.all(population == 0)  # The input population is not modified
