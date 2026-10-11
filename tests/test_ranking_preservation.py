import pandas as pd
import pytest

from calculate_ranking_preservation import (
    _h,
    calculate_rp,
    calculate_rp_per_intervention_level,
)


@pytest.mark.parametrize(
    "f_i, f_j, metamodel_f_i, metamodel_f_j",
    [
        (10, 0, 11, 1),
        (1, 10, 1, 10),
        (10, 10, 10, 10),
    ],
)
def test_h_returns_one_when_metamodel_agrees_with_model(
    f_i, f_j, metamodel_f_i, metamodel_f_j
):
    assert _h(f_i, f_j, metamodel_f_i, metamodel_f_j) == 1


def test_h_returns_zero_when_metamodel_disagrees_with_model():
    assert _h(10, 0, 0, 10) == 0


@pytest.mark.parametrize(
    "evaluations_from_model, evaluations_from_metamodel, expected_rp",
    [
        ([10, 20, 30], [11, 21, 31], 1),
        ([30, 20, 10], [11, 21, 31], 0),
        ([10, 20, 30], [11, 31, 21], pytest.approx(2 / 3)),
        ([10, 10, 20], [5, 6, 5], pytest.approx(2 / 3)),
        ([-3, -1, 2], [-2, 0, 4], 1),
    ],
)
def test_calculate_rp_returns_expected_value(
    evaluations_from_model, evaluations_from_metamodel, expected_rp
):
    assert calculate_rp(evaluations_from_model, evaluations_from_metamodel) == (
        expected_rp
    )


def test_rp_per_intervention_level_reports_levels_average_and_total():
    db = pd.DataFrame(
        {
            "lvl": [1, 1, 1, 5, 5, 5],
            "total_volume_swmm": [10, 20, 30, 1, 2, 3],
            "total_volume_metamodel": [11, 21, 31, 3, 2, 1],
        }
    )
    rp_df = calculate_rp_per_intervention_level(db).set_index("lvl")["RP"]

    assert rp_df[1] == 1
    assert rp_df[5] == 0
    assert rp_df["average"] == 0.5
    # Across levels, the pairs between the two groups are all concordant
    assert rp_df["total"] == pytest.approx((3 + 0 + 9) / 15)
