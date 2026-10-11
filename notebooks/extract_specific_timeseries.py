import pandas as pd
from pathlib import Path


def load_variable_time_series(csv_path: Path, main_col: str, secondary_col: str):
    if not csv_path.exists():
        print(f"Skipping missing file: {csv_path}")
        return None, None

    df = pd.read_csv(csv_path, index_col=0)

    main_s = df[main_col] if main_col in df.columns else None
    sec_s = df[secondary_col] if secondary_col in df.columns else None

    if main_s is None:
        print(f"Missing column '{main_col}' in {csv_path}")
    if sec_s is None:
        print(f"Missing column '{secondary_col}' in {csv_path}")

    return main_s, sec_s


def aggregate_variable_from_multiple_simulations(
    datasplit_type: str,
    indexes: dict,
    intervention_levels: list,
    base_root: Path,
    main_col: str,
    secondary_col: str,
    variable: str,
):
    base_dir = base_root / datasplit_type
    main_series = {}
    secondary_series = {}

    for idx in indexes[datasplit_type]:
        for level in intervention_levels:
            run_id = f"{idx}_{level}"
            csv_path = base_dir / f"id_{idx}_{level}" / (variable + ".csv")

            main_s, sec_s = load_variable_time_series(csv_path, main_col, secondary_col)
            if main_s is not None:
                main_series[run_id] = main_s
            if sec_s is not None:
                secondary_series[run_id] = sec_s

    variable_first_given_column = pd.DataFrame(main_series)
    variable_second_given_column = pd.DataFrame(secondary_series)

    ordered_cols = [
        f"{idx}_{level}"
        for idx in indexes[datasplit_type]
        for level in intervention_levels
    ]
    variable_first_given_column = variable_first_given_column.reindex(
        columns=[c for c in ordered_cols if c in variable_first_given_column.columns]
    )
    variable_second_given_column = variable_second_given_column.reindex(
        columns=[c for c in ordered_cols if c in variable_second_given_column.columns]
    )

    return variable_first_given_column, variable_second_given_column
