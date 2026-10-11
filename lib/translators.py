"""
Translation between BGI configurations (genes) and SWMM input files.

A gene is a list of integer triplets, one per subcatchment, with one position per area
type (green areas, roofs and roads). The value of each position selects the BGI installed
in that area (Chapter 5, Section 5.2.2):
- Green areas: 0 = none, 1 = soakaway, 2 = bio-retention system, 3 = dry swale.
- Roofs: 0 = none, 1 = extensive green roof, 2 = intensive green roof, 3 = cistern.
- Roads: 0 = none, any value > 0 = permeable pavement.
A BGI always occupies all the area available for it in the subcatchment.
"""

import copy

import numpy as np


class BGITranslator:
    def __init__(self, network_data):
        self.network_data = network_data

    def gen_to_inp(self, gen):
        """Return the lines of the .inp file with the BGIs of gen in [LID_USAGE]."""
        lines = copy.deepcopy(self.network_data.original_lines)

        # indices and values of nonzeros
        idx = gen.nonzero().flatten()
        vals = gen[idx]

        new_lines = []
        current_treated_area = {sid: 0 for sid in self.network_data.subcatchment_ids}

        for i, v in zip(idx.tolist(), vals.tolist()):
            new_line, current_treated_area = self.get_LID_inp_line(
                i, v, current_treated_area
            )
            new_lines.append(new_line)

        start = self.network_data.lid_usage_index + 3
        lines[start:start] = new_lines
        return lines

    def get_LID_inp_line(self, inx, val, current_treated_area):
        """Generate an LID usage input line for the SWMM file."""
        indx_subcatchment = inx // 3
        type_LID_inx = inx % 3

        type_LID = self._get_lid_type(type_LID_inx, val)
        name_subcatchment = self.network_data.subcatchment_ids[indx_subcatchment]

        # Calculate area
        area = self._calculate_lid_area(name_subcatchment, type_LID)
        length = np.round(np.sqrt(area), 1)

        # Calculate treated area and update tracking
        treated_area, current_treated_area = self._calculate_treated_area(
            name_subcatchment, type_LID, current_treated_area
        )

        # Build the line
        line = f"{name_subcatchment}             {type_LID} 1       {area}         {length}       0          {treated_area}       0          *                        *                0       \n"

        return line, current_treated_area

    def _get_lid_type(self, type_LID_inx, val):
        """Get the LID type name based on indices."""
        return self.network_data.available_LIDs[type_LID_inx][(val - 1) % 3 + 1]

    def _calculate_lid_area(self, subcatchment_name, lid_type):
        """Area of the LID: all the area available for it in the subcatchment."""
        formatted_lid_name = lid_type.replace("_", " ")
        allowed_area = self.network_data.allowed_nbs_squared_meters.loc[
            subcatchment_name
        ][formatted_lid_name]
        return float(allowed_area)

    def _calculate_treated_area(
        self, subcatchment_name, lid_type, current_treated_area
    ):
        """Calculate the treated impervious area and update tracking."""
        formatted_lid_name = lid_type.replace("_", " ")
        max_impervious_area = float(
            self.network_data.allowed_impervious_area.loc[subcatchment_name][
                formatted_lid_name
            ]
        )

        if current_treated_area[subcatchment_name] == 100:
            treated_area = 0
        elif max_impervious_area + current_treated_area[subcatchment_name] > 100:
            treated_area = 100 - current_treated_area[subcatchment_name]
            current_treated_area[subcatchment_name] = 100
        else:
            treated_area = max_impervious_area
            current_treated_area[subcatchment_name] += max_impervious_area

        return treated_area, current_treated_area
