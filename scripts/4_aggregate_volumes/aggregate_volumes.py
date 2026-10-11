"""Concatenate the per-individual CSO volumes into one table (run by Snakemake)."""

import pandas as pd

dfs = []
for f in snakemake.input:
    dfs.append(pd.read_csv(f))

combined = pd.concat(dfs, ignore_index=True)
combined.to_csv(snakemake.output[0], index=False)
