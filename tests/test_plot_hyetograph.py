import os

import pytest

from plot_hyetograph import RAINFALL_PATH, create_plot, read_data

pytestmark = pytest.mark.skipif(
    not RAINFALL_PATH.exists(), reason=f"Rainfall data not found at {RAINFALL_PATH}"
)


def test_when_data_is_read_it_has_proper_column_names():
    df = read_data(RAINFALL_PATH)
    assert len(df) > 0
    for column in ["Name", "Date", "Value", "Time"]:
        assert column in df.columns


def test_after_reading_data_that_plot_is_generated(tmp_path):
    output_file = tmp_path / "plot.pdf"

    create_plot(read_data(RAINFALL_PATH), output_file)

    assert os.path.getsize(output_file) > 0
