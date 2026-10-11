"""
Suitability assessment of GNN-based metamodels for BGI allocation (Chapter 5).

Evaluation of the baseline and adapted GNN metamodels against SWMM:
1. Generate random BGI proposals (100 per intervention level).
2. Simulate every proposal with SWMM and with each GNN metamodel.
3. Calculate the total CSO volume of every proposal.
4. Aggregate the CSO volumes of all proposals.
5. Rank the proposals by CSO volume.
6. Calculate the accuracy (Table 5.1) and ranking preservation (Table 5.2) metrics.
7. Plot Figures 5.4 and 5.5.

Run with: snakemake --cores <N>

The dataset of SWMM simulations used to fine-tune the adapted metamodel (20 proposals per
intervention level) is generated with: snakemake --cores <N> fine_tuning_dataset
"""

INTERVENTION_LEVELS = [1, 5, 10, 20, 50]  # Percentage of eligible areas with a BGI
METAMODEL_NAMES = ["baseline_metamodel", "adapted_metamodel"]

# Populations: "v2" for the evaluation and "fine_tuning" for the fine-tuning dataset
POPULATION_SIZES = {"v2": 100, "fine_tuning": 20}
SEED_OFFSETS = {"v2": 0, "fine_tuning": 1000}
IDS = [f"{i:02d}" for i in range(POPULATION_SIZES["v2"])]

# Split of the fine-tuning dataset, per intervention level
FINE_TUNING_SPLITS = {
    "training": [f"{i:02d}" for i in range(10)],
    "validation": [f"{i:02d}" for i in range(10, 15)],
    "testing": [f"{i:02d}" for i in range(15, 20)],
}
FINE_TUNING_VARIABLES = [
    "hydraulic_head",
    "total_inflow",
    "flooding_flow",
    "lateral_inflow",
    "runoff",
    "flow_rate",
    "velocity",
]

POPULATIONS = "saved_objects/saved_populations/populations_BGIs"
SIMULATIONS = "saved_objects/saved_simulations/BGIs"
SPLITTED_DATASETS = "saved_objects/saved_splitted_datasets"
FIGURES = "results/figures"


wildcard_constraints:
    lvl="|".join(str(l) for l in INTERVENTION_LEVELS),
    i=r"\d{2}",
    population="v2|fine_tuning",
    split="training|validation|testing",


# -------------------------
# FINAL TARGETS
# -------------------------
rule all:
    input:
        expand(
            "saved_objects/saved_metrics/metrics_total_volumes_{metamodel_name}.csv",
            metamodel_name=METAMODEL_NAMES,
        ),
        expand(
            "saved_objects/saved_metrics/ranking_preservation_{metamodel_name}.csv",
            metamodel_name=METAMODEL_NAMES,
        ),
        expand(
            "saved_objects/saved_ranks/BGIs/metamodel/ranks_{metamodel_name}.csv",
            metamodel_name=METAMODEL_NAMES,
        ),
        f"{FIGURES}/cso_volumes.pdf",
        f"{FIGURES}/rank_comparison.pdf",


rule fine_tuning_dataset:
    input:
        [
            expand(
                f"{SPLITTED_DATASETS}/{split}/id_{{i}}_{{lvl}}/{{variable}}.csv",
                i=ids,
                lvl=INTERVENTION_LEVELS,
                variable=FINE_TUNING_VARIABLES,
            )
            for split, ids in FINE_TUNING_SPLITS.items()
        ],


# -------------------------
# 1. GENERATE POPULATION
# -------------------------
rule generate_random_population:
    input:
        script="scripts/1_generate_populations/generate_random_population.py",
    output:
        f"{POPULATIONS}/population_mutated_{{lvl}}_percent_{{population}}.csv",
    params:
        population_size=lambda wildcards: POPULATION_SIZES[wildcards.population],
        seed=lambda wildcards: int(wildcards.lvl) + SEED_OFFSETS[wildcards.population],
    shell:
        "python {input.script} {params.population_size} {wildcards.lvl} {output} --seed {params.seed}"


# -------------------------
# 2. RUN SIMULATIONS
# -------------------------
rule simulate_population_with_swmm:
    input:
        script="scripts/2_run_simulations/run_swmm.py",
        csv=f"{POPULATIONS}/population_mutated_{{lvl}}_percent_{{population}}.csv",
    output:
        f"{SIMULATIONS}/SWMM/population_mutated_{{lvl}}_percent_{{population}}/id_{{i}}/input.out",
    params:
        output_directory=f"{SIMULATIONS}/SWMM/population_mutated_{{lvl}}_percent_{{population}}/id_{{i}}",
    shell:
        "python {input.script} {input.csv} {wildcards.i} {params.output_directory}"


rule simulate_population_with_metamodel:
    input:
        script="scripts/2_run_simulations/run_metamodel.py",
        csv=f"{POPULATIONS}/population_mutated_{{lvl}}_percent_v2.csv",
    output:
        heads_out=expand(
            f"{SIMULATIONS}/metamodels/{{{{metamodel_name}}}}/population_mutated_{{{{lvl}}}}_percent_v2/id_{{i}}/heads.csv",
            i=IDS,
        ),
        flows_out=expand(
            f"{SIMULATIONS}/metamodels/{{{{metamodel_name}}}}/population_mutated_{{{{lvl}}}}_percent_v2/id_{{i}}/flows.csv",
            i=IDS,
        ),
    params:
        output_dir=f"{SIMULATIONS}/metamodels/{{metamodel_name}}/population_mutated_{{lvl}}_percent_v2",
    shell:
        "python {input.script} {input.csv} {wildcards.metamodel_name} {params.output_dir}"


# -------------------------
# 3. CALCULATE TOTAL CSO VOLUMES
# -------------------------
rule calculate_cso_volumes_single_files:
    input:
        script="scripts/3_calculate_volumes/calculate_cso_volumes.py",
        swmm_out_file=f"{SIMULATIONS}/SWMM/population_mutated_{{lvl}}_percent_v2/id_{{i}}/input.out",
        metamodel_csv_file=f"{SIMULATIONS}/metamodels/{{metamodel_name}}/population_mutated_{{lvl}}_percent_v2/id_{{i}}/flows.csv",
    output:
        "saved_objects/saved_objectives/{metamodel_name}/volumes_population_mutated_{lvl}_percent_id_{i}.csv",
    shell:
        "python {input.script} {input.swmm_out_file} {input.metamodel_csv_file} {wildcards.lvl} {wildcards.i} {output}"


# -------------------------
# 4. AGGREGATE CSO VOLUMES
# -------------------------
rule aggregate:
    input:
        expand(
            "saved_objects/saved_objectives/{{metamodel_name}}/volumes_population_mutated_{lvl}_percent_id_{i}.csv",
            lvl=INTERVENTION_LEVELS,
            i=IDS,
        ),
    output:
        "saved_objects/saved_objectives/aggregated_volumes_{metamodel_name}.csv",
    script:
        "scripts/4_aggregate_volumes/aggregate_volumes.py"


# -------------------------
# 5. CALCULATE RANKS
# -------------------------
rule calculate_ranks:
    input:
        script="scripts/5_generate_ranks/generate_ranks.py",
        input_file="saved_objects/saved_objectives/aggregated_volumes_{metamodel_name}.csv",
    output:
        "saved_objects/saved_ranks/BGIs/metamodel/ranks_{metamodel_name}.csv",
    shell:
        "python {input.script} {input.input_file} {output}"


# -------------------------
# 6. CALCULATE METRICS
# -------------------------
rule total_volume_error_metrics:
    input:
        script="scripts/6_calculate_metrics/calculate_volume_error_metrics.py",
        input_file="saved_objects/saved_objectives/aggregated_volumes_{metamodel_name}.csv",
    output:
        "saved_objects/saved_metrics/metrics_total_volumes_{metamodel_name}.csv",
    shell:
        "python {input.script} {input.input_file} {output}"


rule ranking_preservation:
    input:
        script="scripts/6_calculate_metrics/calculate_ranking_preservation.py",
        input_file="saved_objects/saved_objectives/aggregated_volumes_{metamodel_name}.csv",
    output:
        "saved_objects/saved_metrics/ranking_preservation_{metamodel_name}.csv",
    shell:
        "python {input.script} {input.input_file} {output}"


# -------------------------
# 7. FIGURES
# -------------------------
rule plot_cso_volumes:
    input:
        script="scripts/visualization/plot_cso_volumes.py",
        base="saved_objects/saved_objectives/aggregated_volumes_baseline_metamodel.csv",
        adapted="saved_objects/saved_objectives/aggregated_volumes_adapted_metamodel.csv",
    output:
        f"{FIGURES}/cso_volumes.pdf",
    shell:
        "python {input.script} {input.base} {input.adapted} {output}"


rule plot_rank_comparison:
    input:
        script="scripts/visualization/plot_rank_comparison.py",
        base="saved_objects/saved_ranks/BGIs/metamodel/ranks_baseline_metamodel.csv",
        adapted="saved_objects/saved_ranks/BGIs/metamodel/ranks_adapted_metamodel.csv",
    output:
        f"{FIGURES}/rank_comparison.pdf",
    shell:
        "python {input.script} {input.base} {input.adapted} {output}"


# -------------------------
# FINE-TUNING DATASET
# -------------------------
rule organize_fine_tuning_dataset:
    input:
        f"{SIMULATIONS}/SWMM/population_mutated_{{lvl}}_percent_fine_tuning/id_{{i}}/input.out",
    output:
        f"{SPLITTED_DATASETS}/{{split}}/id_{{i}}_{{lvl}}/input.out",
    shell:
        "cp $(dirname {input})/input.* $(dirname {output})/"


rule extract_fine_tuning_timeseries:
    input:
        script="scripts/fine_tuning_dataset/extract_simulation_timeseries.py",
        out_file=f"{SPLITTED_DATASETS}/{{split}}/id_{{i}}_{{lvl}}/input.out",
    output:
        f"{SPLITTED_DATASETS}/{{split}}/id_{{i}}_{{lvl}}/{{variable}}.csv",
    shell:
        "python {input.script} {input.out_file} {wildcards.variable} {output}"
