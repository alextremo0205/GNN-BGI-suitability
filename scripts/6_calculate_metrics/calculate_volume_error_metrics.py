import argparse
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    mean_absolute_percentage_error,
)


def calculate_metrics_per_intervention_level(db: pd.DataFrame) -> pd.DataFrame:
    metrics = []
    for lvl, group in db.groupby("lvl"):
        y_true = group["total_volume_swmm"]
        y_pred = group["total_volume_metamodel"]
        metrics.append(
            {
                "lvl": lvl,
                "volume_MAE": mean_absolute_error(y_true, y_pred),
                "volume_NSE": r2_score(y_true, y_pred),
                "volume_MAPE_percent": 100
                * mean_absolute_percentage_error(y_true, y_pred),
            }
        )
    metrics_df = pd.DataFrame(metrics).sort_values("lvl").reset_index(drop=True)

    return metrics_df


def add_global_metrics(db, metrics_df):
    y_true = db["total_volume_swmm"]
    y_pred = db["total_volume_metamodel"]
    global_metrics = {
        "lvl": "total",
        "volume_MAE": mean_absolute_error(y_true, y_pred),
        "volume_NSE": r2_score(y_true, y_pred),
        "volume_MAPE_percent": 100 * mean_absolute_percentage_error(y_true, y_pred),
    }
    metrics_df = pd.concat(
        [metrics_df, pd.DataFrame([global_metrics])], ignore_index=True
    )

    return metrics_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str)
    parser.add_argument("out_path", type=str)

    args = parser.parse_args()
    db = pd.read_csv(args.input_file)
    metrics_df = calculate_metrics_per_intervention_level(db)
    metrics_df = add_global_metrics(db, metrics_df)
    metrics_df.to_csv(args.out_path, index=False)
