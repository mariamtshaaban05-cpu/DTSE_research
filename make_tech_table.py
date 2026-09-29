"""
Build a table figure summarizing investment cost, fuel cost, and efficiency
for each technology used by the model, pulled from costs_orca_base.csv.

Technology -> model-carrier mapping (edit TECH_INFO below if your model
uses a different subset, e.g. only onwind and not offwind):
    coal                                          -> Coal
    CCGT, OCGT                                    -> Natural Gas
    onwind, offwind                               -> Wind
    solar-utility, solar-rooftop                  -> Solar
    Lithium-Ion-LFP-bicharger, -store              -> Battery
    BTES_charger, BTES_discharger, granite         -> BTES
"""
import os

import pandas as pd
import matplotlib.pyplot as plt

# Same palette as plot_results_multiple_cases.ipynb, so this table visually
# matches the stacked-bar figures.
color_map = {
    'Solar': '#FDB845',
    'Wind': '#74CBCA',
    'Battery': '#6F4E7C',
    'Natural Gas': '#BFBFBF',
    'Coal': '#8B4513',
    'BTES': '#BF3B3D',
}

# technology (as it appears in costs_orca_base.csv) -> (Category, display name)
TECH_INFO = {
    'coal':                       ('Coal',        'Coal'),
    'CCGT':                       ('Natural Gas',  'Gas (CCGT)'),
#    'OCGT':                       ('Natural Gas',  'Gas (OCGT)'),
    'onwind':                     ('Wind',         'Onshore Wind'),
    #'offwind':                    ('Wind',         'Offshore Wind'),
    'solar-utility':              ('Solar',        'Solar'),
    #'solar-rooftop':              ('Solar',        'Solar (Rooftop)'),
    'Lithium-Ion-LFP-bicharger':  ('Battery',      'Battery (bicharger)'),
    'Lithium-Ion-LFP-store':      ('Battery',      'Battery (Store)'),
    'BTES_charger':               ('BTES',         'BTES (Charger)'),
    'BTES_discharger':            ('BTES',         'BTES (Discharger)'),
    'granite':                    ('BTES',         'BTES (Store)'),
}

# The "fuel" parameter in costs_orca_base.csv is only defined for generic
# fuel carriers (coal, gas, ...), not per individual generator technology
# (CCGT/OCGT both burn "gas", for instance). Map each technology to the
# fuel-carrier row it should pull its fuel cost from; omit technologies
# that don't consume a fuel (renewables, storage).
FUEL_LOOKUP = {
    'coal': 'coal',
    'CCGT': 'gas',
    'OCGT': 'gas',
}

df = pd.read_csv('/Users/mshaaban/clab_underground_th_storage/input_files/costs_orca_base.csv')

inv = df[df['parameter'] == 'investment'].set_index('technology')
eff = df[df['parameter'] == 'efficiency'].set_index('technology')
fuel = df[df['parameter'] == 'fuel'].set_index('technology')


def format_cost(val, unit):
    """Format a cost value, keeping small values (e.g. 0.01) visible
    instead of rounding them away to 0."""
    if pd.isna(val):
        return "–"
    if abs(val) < 1:
        # show enough decimal places to keep small values legible
        return f"{val:,.2f} {unit}"
    return f"{val:,.0f} {unit}"


rows = []
for tech, (category, display_name) in TECH_INFO.items():
    inv_val = inv['value'].get(tech)
    inv_unit = inv['unit'].get(tech, '')
    eff_val = eff['value'].get(tech)

    fuel_tech = FUEL_LOOKUP.get(tech)
    if fuel_tech is not None:
        fuel_val = fuel['value'].get(fuel_tech)
        fuel_unit = fuel['unit'].get(fuel_tech, '')
        fuel_str = f"{fuel_val:,.1f} {fuel_unit}" if pd.notna(fuel_val) else "–"
    else:
        fuel_str = "–"

    cost_str = format_cost(inv_val, inv_unit)
    eff_str = f"{eff_val * 100:.0f}%" if pd.notna(eff_val) else "–"

    rows.append({
        'Category': category,
        'Technology': display_name,
        'Investment Cost': cost_str,
        'Fuel Cost': fuel_str,
        'Efficiency': eff_str,
    })

table_df = pd.DataFrame(rows)
# Keep categories grouped together, in the same order as STACK_ORDER used
# in plot_results_multiple_cases.ipynb.
category_order = ['Wind', 'Solar', 'Natural Gas', 'Coal', 'Battery', 'BTES']
table_df['Category'] = pd.Categorical(table_df['Category'], categories=category_order, ordered=True)
table_df = table_df.sort_values('Category').reset_index(drop=True)

# ---- Render as a figure ----
n_rows = len(table_df)
col_labels = ['Technology', 'Investment Cost', 'Fuel Cost', 'Efficiency']

fig, ax = plt.subplots(figsize=(8.5, 0.45 * n_rows + 1))
ax.axis('off')

table = ax.table(
    cellText=table_df[col_labels].values,
    colLabels=col_labels,
    cellLoc='center',
    colLoc='center',
    loc='center',
)
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 1.8)

# Style header row
for j in range(len(col_labels)):
    cell = table[0, j]
    cell.set_facecolor('#333333')
    cell.set_text_props(color='white', fontweight='bold')

# Color-code each row by category (a colored left-edge stripe via the
# Technology cell's facecolor, tinted so text stays readable) and left-align
# the technology name.
for i, cat in enumerate(table_df['Category']):
    color = color_map.get(str(cat), '#CCCCCC')
    row = i + 1  # +1 to skip header row
    tech_cell = table[row, 0]
    tech_cell.set_facecolor(color)
    tech_cell.set_text_props(ha='left')
    tech_cell.PAD = 0.05
    for j in (1, 2, 3):
        table[row, j].set_facecolor('#F7F7F7' if i % 2 == 0 else '#FFFFFF')

fig.suptitle('Technology Cost and Efficiency', fontsize=14, y=0.98)

out_dir = 'figures'
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'technology_cost_efficiency_table.pdf')
fig.savefig(out_path, bbox_inches='tight', dpi=200)
fig.savefig(out_path.replace('.pdf', '.png'), bbox_inches='tight', dpi=200)
print(f"Saved to {out_path}")