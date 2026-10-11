import pandas as pd
import pytest

from calculate_cso_volumes import get_volume_from_column_ML, m3_to_ML
from calculate_volume_error_metrics import (
    add_global_metrics,
    calculate_metrics_per_intervention_level,
)
from generate_ranks import generate_ranks


@pytest.fixture
def aggregated_volumes():
    return pd.DataFrame(
        {
            "lvl": [1, 1, 5, 5],
            "id": [0, 1, 0, 1],
            "total_volume_metamodel": [1.0, 2.0, 3.0, 5.0],
            "total_volume_swmm": [1.0, 2.0, 4.0, 4.0],
        }
    )


def test_volume_m3_to_million_litres():
    assert m3_to_ML(1) == 0.001


def test_constant_flow_of_one_m3_per_second_during_ten_minutes():
    # Flow time series reported every minute
    series = pd.Series([1.0] * 11)
    assert get_volume_from_column_ML(series) == pytest.approx(600 * 1e-3)


def test_metrics_are_reported_per_level_and_in_total(aggregated_volumes):
    metrics_df = calculate_metrics_per_intervention_level(aggregated_volumes)
    metrics_df = add_global_metrics(aggregated_volumes, metrics_df).set_index("lvl")

    assert list(metrics_df.index) == [1, 5, "total"]
    assert metrics_df.loc[1, "volume_MAE"] == 0
    assert metrics_df.loc[5, "volume_MAE"] == 1
    assert metrics_df.loc["total", "volume_MAE"] == 0.5
    assert metrics_df.loc[1, "volume_MAPE_percent"] == 0
    assert metrics_df.loc[5, "volume_MAPE_percent"] == pytest.approx(25)
    assert metrics_df.loc[1, "volume_NSE"] == 1


def test_ranks_are_ascending_in_volume(aggregated_volumes):
    ranks = generate_ranks(aggregated_volumes)

    assert list(ranks.columns) == ["lvl", "metamodel_rank", "swmm_rank"]
    assert list(ranks["metamodel_rank"]) == [1, 2, 3, 4]
    assert list(ranks["swmm_rank"]) == [1, 2, 3.5, 3.5]
