import pandas as pd

def x_labeling(ax, technology, x_values, fontsize):
    """
    Function to set the x-axis labels for the plot.
    """
    x_vals_max = x_values.iloc[-1] if type(x_values) == pd.Series else x_values[-1]

    if not "BTES_" in technology:
        xticks = [0, 20, 40, 60, 80, 100, 120, 140, 160]
    else:
        # Add % to the x-axis labels but keep them arbitrary
        if 'granite' in technology:
            step = 1000
        elif 'BTES_charger' in technology:
            step = 100
        else:
            step = 25

        xticks = list(range(0, int(x_vals_max) + 1, step))
        if 100 not in xticks:
            xticks = sorted(xticks + [100])

    # Set the x-axis limits
    ax.set_xlim(0, x_vals_max)

    # Add the value 100 to the xticks
    ax.set_xticks(xticks)
    labels = [f"{i}%" for i in xticks]
    ax.set_xticklabels(labels, fontsize=fontsize)

    # Make only the 100% tick bold
    for label in ax.get_xticklabels():
        if label.get_text() == '100%':
            label.set_fontweight('bold')
    return ax