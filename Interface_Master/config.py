"""Shared configuration for the Cervicheck interface.

Anything derived from the pad count lives here so that changing the number of
pads is a one-line edit. Previously the dataframe row template was spelled out
independently in Master.py and in gui.py's reset(); the two drifted apart during
the 7 -> 8 pad migration, which left reset() rebuilding a 12-row frame that the
next sweep (13 values) could not be inserted into.
"""

import numpy as np
import pandas as pd

# Number of pads on the flex PCB, labelled 0 .. PAD_COUNT-1.
PAD_COUNT = 8

# Stretch ratio at no applied pressure. The tissue is unstretched, so this is the
# built-in (strain=1, stress=0) anchor point that align_data() always prepends.
ANCHOR_STRAIN = 1.0

# Stretch ratio of every pad position on the flex PCB, front (nearest, least
# stretched) to back. Pads are added at the FRONT, so a smaller PAD_COUNT drops
# entries from the head of this list: at 7 pads the 1.3375 position does not
# exist and is excluded.
PAD_STRAIN_RATIOS = [1.3375, 1.7375, 1.9375, 2.0375, 2.1375, 2.2375, 2.3375, 2.4375]

if not 1 <= PAD_COUNT <= len(PAD_STRAIN_RATIOS):
    raise ValueError(
        f"PAD_COUNT={PAD_COUNT} has no stretch ratios defined; "
        f"PAD_STRAIN_RATIOS covers 1..{len(PAD_STRAIN_RATIOS)} pads"
    )

# Anchor followed by the stretch ratio of each active pad. Length is
# PAD_COUNT + 1, matching the pressure array built in communication.pressureSweep().
STRAIN_RATIOS = np.array([ANCHOR_STRAIN, *PAD_STRAIN_RATIOS[-PAD_COUNT:]])

# Fitted values reported per sweep, appended below the per-pad rows.
FIT_ROW_LABELS = ['α', 'C', 'Effective Modulus', "Young's Modulus", 'Time (ms)']

# Row labels for the 'Pad number' index column of the results dataframe.
ROW_LABELS = [*range(PAD_COUNT), *FIT_ROW_LABELS]


def new_dataframe():
    """Return an empty results dataframe with only the 'Pad number' column."""
    return pd.DataFrame({'Pad number': list(ROW_LABELS)})


def reset_dataframe(df):
    """Clear `df` in place and restore just the 'Pad number' column.

    Mutates in place because the dataframe is shared by reference across the GUI;
    rebinding it here would leave the other holders pointing at the stale frame.
    """
    df.drop(df.index, inplace=True)
    df.drop(df.columns, axis=1, inplace=True)
    df.insert(0, 'Pad number', list(ROW_LABELS))
    return df
