### Calculating wind and solar capacity factors from ERA5 data with Atlite

Activate the environment for obtaining capacity factors with

Then, obtain the capacity factors from ERA5 with Atlite for each year by running

```python get_US_CFs_year.py --year YEAR```

e.g. for YEAR 2023. We use the wind turbine NREL_ReferenceTurbine_2020ATB_4MW for wind capacity factors and CSi panels with single-axis tracking for solar PV capacity factors.
This returns netCDF files for the gridded capacity factors for the contiguous US.

We then only keep the top x percent of grid cells that when averaged (both over space and time) result in an average capacity factor that corresponds to the average capacity factor reported by the [EIA](https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=table_6_07_b) and for those grid cells get the time series of capacity factors averaged spatially over the contiguous US with the interactive notebook

```get_top_xpercent_cfs.ipynb```.
