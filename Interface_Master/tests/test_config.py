"""Headless tests for Interface_Master/config.py and the reset/sweep dataframe cycle.

No hardware and no display required. Run with:
    cd ~/Documents/GitHub/Cervicheck && .venv/bin/python -m pytest <this file> -q
or standalone:
    cd ~/Documents/GitHub/Cervicheck && .venv/bin/python <this file>
"""

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

import config  # noqa: E402


def _sweep_row(pad_count):
    """The `arr` that gui.updateParameters builds: pads[1:] plus the 5 fit values."""
    pressure = np.zeros(pad_count + 1)          # communication.pressureSweep
    return [*pressure[1:], '1', '2', '3', '4', '5']


# --- config invariants -------------------------------------------------------

def test_strain_length_matches_pad_count():
    assert len(config.STRAIN_RATIOS) == config.PAD_COUNT + 1


def test_strain_starts_at_anchor():
    assert config.STRAIN_RATIOS[0] == 1.0


def test_strain_is_strictly_increasing():
    assert np.all(np.diff(config.STRAIN_RATIOS) > 0)


def test_row_labels_length():
    assert len(config.ROW_LABELS) == config.PAD_COUNT + len(config.FIT_ROW_LABELS)


def test_row_labels_are_zero_indexed_pads():
    assert config.ROW_LABELS[:config.PAD_COUNT] == list(range(config.PAD_COUNT))


def test_eight_pad_strain_matches_master_py_literal():
    """The array Master.py used before the config extraction."""
    expected = [1, 1.3375, 1.7375, 1.9375, 2.0375, 2.1375, 2.2375, 2.3375, 2.4375]
    assert config.PAD_COUNT == 8
    assert np.allclose(config.STRAIN_RATIOS, expected)


def test_seven_pad_strain_excludes_1_3375():
    """Dropping to 7 pads must reproduce Master.py's commented-out 7-pad array."""
    expected = [1, 1.7375, 1.9375, 2.0375, 2.1375, 2.2375, 2.3375, 2.4375]
    ratios = np.array([config.ANCHOR_STRAIN, *config.PAD_STRAIN_RATIOS[-7:]])
    assert np.allclose(ratios, expected)
    assert 1.3375 not in ratios


def test_pad_count_out_of_range_is_rejected():
    """A PAD_COUNT with no stretch ratios defined must fail loudly at import."""
    src = (Path(config.__file__)).read_text().replace("PAD_COUNT = 8", "PAD_COUNT = 99", 1)
    ns = {"__name__": "config_bad", "__file__": config.__file__}
    try:
        exec(compile(src, config.__file__, "exec"), ns)
    except ValueError as e:
        assert "PAD_COUNT" in str(e)
    else:
        raise AssertionError("PAD_COUNT=99 was accepted but has no stretch ratios")


# --- the regression that caused the crash ------------------------------------

def test_new_dataframe_shape():
    df = config.new_dataframe()
    assert df.shape == (len(config.ROW_LABELS), 1)
    assert list(df.columns) == ['Pad number']


def test_sweep_row_length_matches_dataframe_index():
    df = config.new_dataframe()
    assert len(_sweep_row(config.PAD_COUNT)) == len(df.index)


def test_reset_then_sweep_does_not_raise():
    """The exact sequence that used to die with 'Length of values (13) ... index (12)'."""
    df = config.new_dataframe()
    df.insert(df.shape[1], 'Sweep 1', _sweep_row(config.PAD_COUNT))

    config.reset_dataframe(df)
    assert list(df.columns) == ['Pad number']
    assert len(df.index) == len(config.ROW_LABELS)

    df.insert(df.shape[1], 'Sweep 1', _sweep_row(config.PAD_COUNT))   # used to ValueError
    assert df.shape == (len(config.ROW_LABELS), 2)


def test_reset_is_idempotent():
    df = config.new_dataframe()
    before = df.shape
    for _ in range(3):
        config.reset_dataframe(df)
    assert df.shape == before


def test_reset_mutates_in_place():
    """reset_dataframe must not rebind; the GUI shares the frame by reference."""
    df = config.new_dataframe()
    df.insert(df.shape[1], 'Sweep 1', _sweep_row(config.PAD_COUNT))
    same = df
    config.reset_dataframe(df)
    assert same is df
    assert list(same.columns) == ['Pad number']


def test_reset_matches_fresh_dataframe():
    df = config.new_dataframe()
    df.insert(df.shape[1], 'Sweep 1', _sweep_row(config.PAD_COUNT))
    config.reset_dataframe(df)
    pd.testing.assert_frame_equal(df, config.new_dataframe())


# --- delete() column bookkeeping (pure pandas half of gui.delete) ------------

def _simulate_delete(df, index, j):
    df.drop(df.columns[index + 1], axis=1, inplace=True)
    for i in range(index, j - 2):
        df.rename(columns={df.columns[i + 1]: 'Sweep ' + str(i + 1)}, inplace=True)


def test_delete_middle_sweep_renumbers_columns():
    df = config.new_dataframe()
    for n in (1, 2, 3):
        df.insert(df.shape[1], f'Sweep {n}', _sweep_row(config.PAD_COUNT))
    _simulate_delete(df, index=1, j=4)
    assert list(df.columns) == ['Pad number', 'Sweep 1', 'Sweep 2']


def test_delete_first_sweep_renumbers_columns():
    df = config.new_dataframe()
    for n in (1, 2, 3):
        df.insert(df.shape[1], f'Sweep {n}', _sweep_row(config.PAD_COUNT))
    _simulate_delete(df, index=0, j=4)
    assert list(df.columns) == ['Pad number', 'Sweep 1', 'Sweep 2']


def test_delete_last_sweep_leaves_others_alone():
    df = config.new_dataframe()
    for n in (1, 2, 3):
        df.insert(df.shape[1], f'Sweep {n}', _sweep_row(config.PAD_COUNT))
    _simulate_delete(df, index=2, j=4)
    assert list(df.columns) == ['Pad number', 'Sweep 1', 'Sweep 2']


def test_delete_preserves_column_data():
    """Renaming must not shuffle which values belong to which sweep."""
    df = config.new_dataframe()
    for n in (1, 2, 3):
        row = [*[float(n)] * config.PAD_COUNT, 'a', 'b', 'c', 'd', 'e']
        df.insert(df.shape[1], f'Sweep {n}', row)
    _simulate_delete(df, index=0, j=4)          # drop Sweep 1
    assert df['Sweep 1'].iloc[0] == 2.0         # old Sweep 2 renamed to Sweep 1
    assert df['Sweep 2'].iloc[0] == 3.0


# --- integration with the fitting pipeline -----------------------------------

def test_align_data_anchor_with_config_strain():
    from data_analysis import align_data
    pressure = np.zeros(config.PAD_COUNT + 1)
    pressure[3] = -4.2
    x, y = align_data(config.STRAIN_RATIOS, pressure)
    assert x[0] == 1.0 and y[0] == 0.0
    assert len(x) == 2
    assert np.count_nonzero(x == 1.0) == 1      # anchor not double-counted


def test_full_fit_runs_with_config_strain():
    from data_analysis import align_data, analyze_data
    pressure = np.zeros(config.PAD_COUNT + 1)
    pressure[2:6] = [-2.1, -4.2, -6.3, -8.4]
    x, y = align_data(config.STRAIN_RATIOS, pressure)
    popt, eff, youngs, intercept = analyze_data(x, y)
    assert len(popt) == 2
    assert all(np.isfinite(v) for v in (*popt, eff, youngs, intercept))


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception as e:
            failed += 1
            print(f"FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
