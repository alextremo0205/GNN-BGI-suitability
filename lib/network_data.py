"""
Network data for Blue-Green Infrastructure (BGI) experiments.

BGINetworkDataLoader reads, from the network folder (e.g. data/Loenen - v8):
- <network>.inp: the SWMM model, with an empty [LID_USAGE] section.
- implementation_details.xlsx: allowed BGI area and treated impervious area per subcatchment.
- runoffs_subcatchments_with_BGIs/: lateral inflows of the baseline system and of every
  BGI combination per subcatchment (the runoff lookup tables used by the metamodel).
  They are produced by scripts/0_preprocessing/build_bgi_runoff_lookup_tables.ipynb.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import swmmio

# Codes of the BGI combinations in the runoff lookup tables. Codes 1-3 are BGIs in green
# areas, 4-6 on roofs and 7 on roads (see BGITranslator for the gene encoding).
SINGLE_BGI_CODES = ["1", "2", "3", "4", "5", "6", "7"]
DOUBLE_BGI_CODES = [
    "1_4", "1_5", "1_6", "1_7",
    "2_4", "2_5", "2_6", "2_7",
    "3_4", "3_5", "3_6", "3_7",
    "4_7", "5_7", "6_7",
]  # fmt: skip
TRIPLE_BGI_CODES = [
    "1_4_7", "1_5_7", "1_6_7",
    "2_4_7", "2_5_7", "2_6_7",
    "3_4_7", "3_5_7", "3_6_7",
]  # fmt: skip


@dataclass
class BGINetworkData:
    # Basic network information
    n_subcatchments: int
    subcatchment_ids: List[str]

    # Network paths and identifiers
    network_name: str
    inp_path: Path
    folder_path: Path

    # LID information
    available_LIDs: List[Dict[int, str]]

    # Input file
    original_lines: List[str]
    lid_usage_index: Optional[int]

    # Allowed BGI implementation per subcatchment
    allowed_impervious_area: pd.DataFrame
    allowed_nbs_squared_meters: pd.DataFrame

    # Runoff lookup tables (lateral inflows) for the metamodel
    baseline_lat_inflows: Optional[pd.DataFrame] = None
    hash_table_inflows: Optional[Dict[str, pd.DataFrame]] = None

    def __str__(self):
        return (
            f"BGINetworkData(name={self.network_name}, "
            f"subcatchments={self.n_subcatchments}, "
            f"folder={self.folder_path})"
        )


class BGINetworkDataLoader:
    def __init__(self, folder: Path):
        self.folder = folder.resolve()
        self.network = self.folder.name
        self.inp_path = self.folder / f"{self.network}.inp"
        self.runoffs_folder = self.folder / "runoffs_subcatchments_with_BGIs"

    def load_network_data(self, load_runoff_lookup: bool = True) -> BGINetworkData:
        """Return a BGINetworkData object with all necessary information.

        Set load_runoff_lookup=False when the runoff lookup tables are not needed
        (SWMM simulations) or do not exist yet (while building them).
        """
        n_subcatchments, subcatchment_ids = self._get_basic_network_info()
        original_lines, lid_usage_index = self._process_input_file()
        allowed_impervious_area, allowed_nbs_squared_meters = (
            self._load_implementation_details()
        )

        baseline_lat_inflows, hash_table_inflows = None, None
        if load_runoff_lookup:
            baseline_lat_inflows = self._get_baseline_lateral_inflows()
            hash_table_inflows = self._get_hash_table_inflows()

        return BGINetworkData(
            n_subcatchments=n_subcatchments,
            subcatchment_ids=subcatchment_ids,
            network_name=self.network,
            inp_path=self.inp_path,
            folder_path=self.folder,
            available_LIDs=self._define_available_lids(),
            original_lines=original_lines,
            lid_usage_index=lid_usage_index,
            allowed_impervious_area=allowed_impervious_area,
            allowed_nbs_squared_meters=allowed_nbs_squared_meters,
            baseline_lat_inflows=baseline_lat_inflows,
            hash_table_inflows=hash_table_inflows,
        )

    def _get_baseline_lateral_inflows(self):
        return pd.read_csv(
            self.runoffs_folder / "swmm_baseline" / "lateral_inflow_0.csv",
            index_col=0,
        )

    def _get_hash_table_inflows(self):
        folders = {
            "inps_single_BGI": SINGLE_BGI_CODES,
            "inps_double_BGI": DOUBLE_BGI_CODES,
            "inps_triple_BGI": TRIPLE_BGI_CODES,
        }
        hash_table_inflows = {}
        for folder, codes in folders.items():
            for code in codes:
                hash_table_inflows[code] = pd.read_csv(
                    self.runoffs_folder
                    / folder
                    / "lateral_inflows"
                    / f"lateral_inflow_{code}.csv",
                    index_col=0,
                )
        return hash_table_inflows

    def _get_basic_network_info(self):
        """Extract basic network information from the hydraulic model."""
        hydraulic_model = swmmio.Model(self.inp_path)
        n_subcatchments = len(hydraulic_model.inp.subcatchments)
        subcatchment_ids = list(hydraulic_model.inp.subcatchments.index)
        return n_subcatchments, subcatchment_ids

    def _process_input_file(self):
        """Read the input file and find the [LID_USAGE] section."""
        original_lines = _extract_lines_from_inp(self.inp_path)
        lid_usage_index = next(
            (
                i
                for i, line in enumerate(original_lines)
                if line.strip() == "[LID_USAGE]"
            ),
            None,
        )
        return original_lines, lid_usage_index

    def _load_implementation_details(self):
        """Load allowed BGI areas from the implementation details Excel file."""
        excel_file_path = self.folder / "implementation_details.xlsx"

        allowed_impervious_area = pd.read_excel(
            excel_file_path, sheet_name="Allowed_imperviousness_area (%)", header=1
        )
        allowed_impervious_area.rename(
            columns={"Unnamed: 0": "Subcatchment_ID"}, inplace=True
        )
        allowed_impervious_area.set_index("Subcatchment_ID", inplace=True)

        allowed_nbs_squared_meters = pd.read_excel(
            excel_file_path, sheet_name="Allowed_NBS (m²)", header=1
        )
        allowed_nbs_squared_meters.rename(
            columns={"Unnamed: 0": "Subcatchment_ID"}, inplace=True
        )
        allowed_nbs_squared_meters.set_index("Subcatchment_ID", inplace=True)

        return allowed_impervious_area, allowed_nbs_squared_meters

    def _define_available_lids(self):
        """BGI types per gene position: green areas, roofs and roads."""
        return [
            {1: "Soakaway", 2: "Bio_retention_system", 3: "Dry_swale"},
            {1: "Extensive_green_roof", 2: "Intensive_green_roof", 3: "Cistern"},
            {
                1: "Permeable_pavement",
                2: "Permeable_pavement",
                3: "Permeable_pavement",
            },
        ]


def _extract_lines_from_inp(inp_path) -> List[str]:
    """Read the original lines from the inp file."""
    with open(inp_path, "r") as f:
        original_lines = f.readlines()
    return original_lines


def create_bgi_network_loader(folder: Path) -> BGINetworkDataLoader:
    """Create a BGI (Blue-Green Infrastructure) network data loader."""
    return BGINetworkDataLoader(folder)
