import atlite
import cartopy.io.shapereader as shpreader
import geopandas as gpd
from shapely.geometry import box
from argparse import ArgumentParser


def main(year):
    # Get the US geometry
    shpfilename = shpreader.natural_earth(
        resolution="10m", category="cultural", name="admin_0_countries"
    )
    reader = shpreader.Reader(shpfilename)
    US = gpd.GeoSeries(
        {r.attributes["NAME_EN"]: r.geometry for r in reader.records()},
        crs="epsg:4326",  # updated from deprecated {"init": "epsg:4326"}
    ).reindex(["United States of America"])

    # Clip US geometry to the MISO bounding box
    # Covers the Midcontinent Independent System Operator footprint
    miso_bbox = box(minx=-105, miny=28, maxx=-82, maxy=50)
    region = US.geometry.intersection(miso_bbox)
    region_name = "miso"

    # Define the cutout; this will not yet trigger any major operations
    cutout = atlite.Cutout(
        path=f"{region_name}-{year}_V2",
        module="era5",
        bounds=region.unary_union.bounds,
        time=f"{year}",
        chunks={"time": 100},
    )

    # This is where all the work happens (this can take some time).
    cutout.prepare(
        compression={"zlib": True, "complevel": 9},
        monthly_requests=True,
        concurrent_requests=True,
    )

    # Extract wind capacity factors
    # Using 4MW turbine with 110m hub height to match wnd100m ERA5 variable
    wind_power_generation = cutout.wind(
        turbine="NREL_ReferenceTurbine_2020ATB_4MW",
        capacity_factor_timeseries=True,
    )

    # Extract solar capacity factors
    solar_power_generation = cutout.pv(
        panel="CSi",
        orientation="latitude_optimal",
        tracking="horizontal",
        capacity_factor_timeseries=True,
    )

    # Save as NetCDF
    wind_power_generation.to_netcdf(f"{region_name}_wind_CF_timeseries_{year}.nc")
    solar_power_generation.to_netcdf(f"{region_name}_solar_CF_timeseries_{year}.nc")

    print(f"Done. Saved wind and solar CF timeseries for MISO {year}.")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--year", type=int, help="Get data for this year")
    args = parser.parse_args()
    main(args.year)