# Suitability assessment of GNN-based metamodels for BGI allocation

This repository contains the code of Chapter 5 of the PhD thesis:

> Garzón Díaz, J. A. (2026). *Metamodeling of Urban Drainage Systems with Graph Neural Networks* (PhD thesis). Delft University of Technology. Chapter 5: *Suitability assessment of GNN-based metamodels for BGI allocation*. <!-- TODO: add the link to the TU Delft repository -->

The data needed to run it, and the results reported in the chapter, are available at: [4TU Data repository](https://doi.org/10.4121/0562e37c-5af7-41d1-9679-61880878eb46) <!-- TODO: add the link/DOI of the data repository -->

## What this code does

The chapter assesses whether graph neural network (GNN) metamodels are suitable surrogates of SWMM for optimising the allocation of Blue-Green Infrastructure (BGI) in an urban drainage system. Suitability is assessed along two dimensions, for the total combined sewer overflow (CSO) volume of the Loenen (NL) system under a climate-adjusted (2085) design storm with a 2-year return period:

- **Accuracy**: MAE, MAPE and Nash–Sutcliffe efficiency (NSE).
- **Consistency**: ranking preservation (RP), i.e. how often the metamodel orders a pair of proposals as SWMM does.

The workflow (Figure 5.1 of the chapter) consists of:

0. **Surrogate hydrological simulations.** The runoff of every subcatchment is pre-computed with SWMM for the 32 possible BGI combinations per subcatchment (Section 5.2.3).
1. **Interventions.** 100 random BGI proposals are generated for each of five intervention levels: 1, 5, 10, 20 and 50% of the eligible areas (Section 5.2.2).
2. **Simulations.** Every proposal is simulated with SWMM and with the two GNN metamodels.
3. **Total CSO volume** of every proposal, from the flows over the two weirs (Equation 5.1).
4. **Aggregation** of the CSO volumes of the 500 proposals.
5. **Ranking** of the proposals by CSO volume, according to SWMM and to each metamodel.
6. **Evaluation**: accuracy (Table 5.1) and ranking preservation (Table 5.2), per intervention level and overall.
7. **Figures** 5.4 (CSO volumes) and 5.5 (rank comparison).

The two metamodels evaluated are:

| Name in the code | Chapter 5 | Description |
| --- | --- | --- |
| `baseline_metamodel` | Base metamodel | Best metamodel of Chapter 4 (*Joined tasks, fully fine-tuned*), used as-is. |
| `adapted_metamodel` | Adapted metamodel | Baseline metamodel with an additional decoder for the flows over the weirs, trained with the baseline weights frozen, followed by fine-tuning of all weights. |

The adapted metamodel was trained in the [SWMM_GNN_Metamodel](https://github.com/alextremo0205/SWMM_GNN_Metamodel) repository, on a dataset of 100 SWMM simulations (20 per intervention level) generated with this workflow (see [Fine-tuning dataset](#fine-tuning-dataset)).

### BGI proposals

A proposal is a list of integer triplets, one per subcatchment, with one entry per area type (green areas, roofs and roads):

| Area type | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| Green areas | No BGI | Soakaway | Bio-retention system | Dry swale |
| Roofs | No BGI | Extensive green roof | Intensive green roof | Cistern |
| Roads | No BGI | Permeable pavement | | |

Each BGI occupies all the area available for it in the subcatchment (`implementation_details.xlsx`). The populations sample values 1–3 for every area type; for roads, any value above 0 is a permeable pavement.

## Repository structure

```text
├── Snakefile                  # Workflow of steps 1-6
├── lib/                       # Shared code
│   ├── network_data.py        #   Loading of the network and the BGI data
│   ├── translators.py         #   BGI configuration (gene) -> SWMM .inp file
│   ├── simulators.py          #   SWMM and GNN metamodel simulators
│   ├── paths.py               #   Paths, read from the .env file
│   └── ...
├── scripts/
│   ├── 0_preprocessing/       # Runoff lookup tables for the metamodel
│   ├── 1_generate_populations/
│   ├── 2_run_simulations/
│   ├── 3_calculate_volumes/
│   ├── 4_aggregate_volumes/
│   ├── 5_generate_ranks/
│   ├── 6_calculate_metrics/
│   ├── fine_tuning_dataset/   # Dataset to fine-tune the adapted metamodel
│   └── visualization/         # Figures 5.3, 5.4 and 5.5
├── notebooks/                 # Tables 5.1-5.2 and CSO distributions of the fine-tuning dataset
└── tests/
```

## Setup

### 1. Code

Clone this repository and the repository of the GNN metamodel, which provides the model architecture:

```bash
git clone https://github.com/alextremo0205/GNN-BGI-suitability.git
git clone https://github.com/alextremo0205/SWMM_GNN_Metamodel.git
```

The results of the chapter were obtained with commit `b374459` of `SWMM_GNN_Metamodel`.

### 2. Environment

The environment is managed with [uv](https://docs.astral.sh/uv/) and uses Python 3.12:

```bash
cd GNN-BGI-suitability
uv sync
```

Then, either activate it (`source .venv/bin/activate`) or prefix the commands below with `uv run`.

### 3. Data

Download the [data repository](<!-- TODO: add the link/DOI of the data repository -->) and copy its folders (`data/`, `saved_objects/` and `results/`) into the root of this repository. Its README describes every file. It contains the inputs below, as well as the CSO volumes, ranks, metrics and figures of the chapter:

```text
data/
└── Loenen - v8/
    ├── Loenen - v8.inp                       # SWMM model, including the design storm
    ├── implementation_details.xlsx           # Allowed BGI areas per subcatchment
    ├── Composite_rainfall_2085_2_years.csv   # Design storm (Figure 5.3)
    ├── runoffs_subcatchments_with_BGIs/      # Runoff lookup tables (step 0)
    └── metamodel_files/                      # Metamodel hyperparameters and weights
saved_objects/
├── saved_normalizers/normalizer_Loenen_v7.pkl   # Normalizer of the metamodel
└── saved_populations/populations_BGIs/          # BGI proposals used in the chapter
    ├── population_mutated_<lvl>_percent_v2.csv           # Evaluation (100 per level)
    └── population_mutated_<lvl>_percent_fine_tuning.csv  # Fine-tuning (20 per level)
```

Then mark the results of the data repository as up to date, so that Snakemake does not generate new random proposals:

```bash
snakemake --touch
```

### 4. Environment variables

Copy `.env_example` to `.env` and set the paths:

```bash
cp .env_example .env
```

| Variable | Description |
| --- | --- |
| `METAMODEL_CODE_PATH` | Folder of the `SWMM_GNN_Metamodel` repository. |
| `DATA_FOLDER_PATH` | Folder that contains `Loenen - v8` (default: `./data`). |
| `SAVED_OBJECTS_FOLDER_PATH` | Folder with the normalizer (default: `./saved_objects`). |
| `RESULTS_FOLDER_PATH` | Folder for the figures (default: `./results`). |

## Usage

### Run the workflow

```bash
snakemake --cores 8
```

The outputs are written to `saved_objects/` and `results/`:

| Step | Output |
| --- | --- |
| 1 | `saved_populations/populations_BGIs/population_mutated_<lvl>_percent_v2.csv` |
| 2 | `saved_simulations/BGIs/{SWMM,metamodels/<metamodel>}/population_mutated_<lvl>_percent_v2/id_<id>/` |
| 3 | `saved_objectives/<metamodel>/volumes_population_mutated_<lvl>_percent_id_<id>.csv` |
| 4 | `saved_objectives/aggregated_volumes_<metamodel>.csv` |
| 5 | `saved_ranks/BGIs/metamodel/ranks_<metamodel>.csv` |
| 6 | `saved_metrics/metrics_total_volumes_<metamodel>.csv` (Table 5.1), `saved_metrics/ranking_preservation_<metamodel>.csv` (Table 5.2) |
| 7 | `results/figures/cso_volumes.pdf` (Figure 5.4), `results/figures/rank_comparison.pdf` (Figure 5.5) |

> [!IMPORTANT]
> Step 1 generates new random populations. To reproduce the results of the chapter, use the populations of the data repository. If you copy them (or any other results) into `saved_objects/`, run `snakemake --touch` first, so that Snakemake considers them up to date instead of generating them again.

Tables 5.1 and 5.2 are summarised in `notebooks/aggregated_metric_calculation.ipynb`.

### Fine-tuning dataset

The SWMM simulations used to fine-tune the adapted metamodel (20 proposals per intervention level, split into 10 for training, 5 for validation and 5 for testing) are generated with:

```bash
snakemake --cores 8 fine_tuning_dataset
```

They are written to `saved_objects/saved_splitted_datasets/{training,validation,testing}/id_<id>_<lvl>/`. Their CSO distributions are shown in `notebooks/cso_distributions_fine_tuning_dataset.ipynb`.

### Runoff lookup tables (step 0)

The lookup tables are included in the data repository. They can be generated again with:

```bash
python scripts/0_preprocessing/build_bgi_runoff_lookup_tables.py
```

### Figures

Figures 5.4 and 5.5 are produced by the workflow. The hyetograph of the design storm (Figure 5.3) is produced with:

```bash
python scripts/visualization/plot_hyetograph.py
```

### Tests

```bash
uv run pytest
```

## License

This code is released under the [MIT License](LICENSE).
