"""Rank all individuals by total CSO volume, according to SWMM and to the metamodel."""

import argparse

import pandas as pd


def generate_ranks(df):
    df["metamodel_rank"] = df["total_volume_metamodel"].rank(ascending=True)
    df["swmm_rank"] = df["total_volume_swmm"].rank(ascending=True)
    filtered_df = df[["lvl", "metamodel_rank", "swmm_rank"]]
    return filtered_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str)
    parser.add_argument("output_file", type=str)

    args = parser.parse_args()

    df = pd.read_csv(args.input_file)
    rank_df = generate_ranks(df)
    rank_df.to_csv(args.output_file)
