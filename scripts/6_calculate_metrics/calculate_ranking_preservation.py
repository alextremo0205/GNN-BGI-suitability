"""Ranking Preservation (RP) of the metamodel total CSO volumes with respect to SWMM.

Chapter 5, Equations 5.7-5.8 and Table 5.2.

RP is reported for all individuals together ("total"), for each intervention level,
and as the average of the per-level values ("average").
"""

import argparse
from math import comb

import pandas as pd


def _h(f_i, f_j, metamodel_i, metamodel_j):
    """Evaluate whether a pair is concordant between model and metamodel outputs.

    A pair ``(i, j)`` is considered concordant when the relative ordering between
    ``f_i`` and ``f_j`` matches the relative ordering between ``metamodel_i`` and
    ``metamodel_j``. Ties are treated as concordant.

    Parameters
    ----------
    f_i : float
        Objective value of individual ``i`` from the reference model.
    f_j : float
        Objective value of individual ``j`` from the reference model.
    metamodel_i : float
        Objective value of individual ``i`` from the metamodel.
    metamodel_j : float
        Objective value of individual ``j`` from the metamodel.

    Returns
    -------
    int
        ``1`` if the pair is concordant, otherwise ``0``.
    """
    if (f_i - f_j) * (metamodel_i - metamodel_j) >= 0:
        return 1
    else:
        return 0


def _calculate_concordant_pairs(f_list, metamodel_list, ND):
    """Count concordant pairs between reference and metamodel evaluation lists.

    Parameters
    ----------
    f_list : list[float]
        Objective values from the reference model.
    metamodel_list : list[float]
        Objective values from the metamodel.
    ND : int
        Number of evaluated individuals considered in both lists.

    Returns
    -------
    int
        Total number of concordant pairs among all ``ND * (ND - 1) / 2`` pairs.
    """
    concordant_pairs = 0
    for i in range(ND):
        for j in range(i + 1, ND):
            concordant_pairs += _h(
                f_list[i],
                f_list[j],
                metamodel_list[i],
                metamodel_list[j],
            )

    return concordant_pairs


def calculate_rp(evals_from_model, evals_from_metamodel):
    """Compute the Ranking Preservation (RP) indicator.

    This metric measures how well the ranking induced by metamodel evaluations
    matches the ranking induced by reference model evaluations, as proposed by
    Díaz-Manríquez et al. (2017).

    Parameters
    ----------
    evals_from_model : list[float]
        Objective values produced by the reference model.
    evals_from_metamodel : list[float]
        Objective values produced by the metamodel for the same individuals and
        in the same order.

    Returns
    -------
    float
        Ratio of concordant pairs over all possible pairs, in the range
        :math:`[0, 1]`.
    """
    ND = len(evals_from_metamodel)
    concordant_pairs = _calculate_concordant_pairs(
        evals_from_model, evals_from_metamodel, ND
    )
    combinations = comb(ND, 2)
    rp = concordant_pairs / combinations
    return rp


def calculate_rp_per_intervention_level(db: pd.DataFrame) -> pd.DataFrame:
    rps = []
    for lvl, group in db.groupby("lvl"):
        rps.append(
            {
                "lvl": lvl,
                "RP": calculate_rp(
                    list(group["total_volume_swmm"]),
                    list(group["total_volume_metamodel"]),
                ),
            }
        )
    rp_df = pd.DataFrame(rps).sort_values("lvl").reset_index(drop=True)
    average_rp = {"lvl": "average", "RP": rp_df["RP"].mean()}
    total_rp = {
        "lvl": "total",
        "RP": calculate_rp(
            list(db["total_volume_swmm"]), list(db["total_volume_metamodel"])
        ),
    }
    return pd.concat([rp_df, pd.DataFrame([average_rp, total_rp])], ignore_index=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str)
    parser.add_argument("out_path", type=str)

    args = parser.parse_args()
    db = pd.read_csv(args.input_file)
    rp_df = calculate_rp_per_intervention_level(db)
    rp_df.to_csv(args.out_path, index=False)
