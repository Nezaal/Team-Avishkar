import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CRATER = ROOT / "dataset/lunar_crater_database_robbins_2018/lunar_crater_database_robbins_2018_bundle/data/lunar_crater_database_robbins_2018.csv"
OHRC = ROOT / "ground_truth/sources/coordinates_ohrc_iit.csv"

# Load craters
craters = pd.read_csv(
    CRATER,
    usecols=[
        "CRATER_ID",
        "LAT_CIRC_IMG",
        "LON_CIRC_IMG",
        "DIAM_CIRC_IMG"
    ]
)

# Load OHRC
ohrc = pd.read_csv(OHRC)

row = ohrc.iloc[0]

print("\nFIRST OHRC SCENE:")
print(row["name"])

latitudes = [
    row["upper_left_latitude"],
    row["upper_right_latitude"],
    row["lower_left_latitude"],
    row["lower_right_latitude"],
]

longitudes = [
    row["upper_left_longitude"],
    row["upper_right_longitude"],
    row["lower_left_longitude"],
    row["lower_right_longitude"],
]

print("\nOHRC latitude:")
print(min(latitudes), "to", max(latitudes))

print("\nOHRC longitude:")
print(min(longitudes), "to", max(longitudes))

# Find craters using ONLY latitude first
lat_matches = craters[
    (craters["LAT_CIRC_IMG"] >= min(latitudes)) &
    (craters["LAT_CIRC_IMG"] <= max(latitudes))
]

print("\nCrater database:")
print("Total:", len(craters))
print("Latitude matches:", len(lat_matches))

# Now longitude using simple 0-360 comparison
lon_matches = lat_matches[
    (lat_matches["LON_CIRC_IMG"] >= min(longitudes)) &
    (lat_matches["LON_CIRC_IMG"] <= max(longitudes))
]

print("Latitude + longitude matches:", len(lon_matches))

print("\nSample matching craters:")
print(
    lon_matches[
        ["CRATER_ID", "LAT_CIRC_IMG", "LON_CIRC_IMG", "DIAM_CIRC_IMG"]
    ].head(20).to_string(index=False)
)