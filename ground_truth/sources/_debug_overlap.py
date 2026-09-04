import pandas as pd, numpy as np, json

with open("ground_truth/product_catalog.json") as f:
    cat = json.load(f)

ohrc = [p for p in cat["products"] if p["sensor"] == "OHRC"]
tmc2 = [p for p in cat["products"] if p["sensor"] == "TMC-2"]

# Non-matching OHRC at lon 43-44
nomatch = [p for p in ohrc if "20200229T0739" in p["product_id"]][0]
bb = nomatch["bounding_box"]
print("OHRC:", nomatch["product_id"])
print("bbox:", bb)

# Check TMC-2 strips that might pass through this region
for t in tmc2:
    df = pd.read_csv(t["geometry_csv"])
    lon_norm = ((df["Longitude"].values + 180) % 360) - 180
    lat = df["Latitude"].values
    # Check if ANY points are near the OHRC lat/lon (within 2 deg)
    near_lat = (lat >= bb["lat_min"] - 2) & (lat <= bb["lat_max"] + 2)
    near_lon = (lon_norm >= bb["lon_min"] - 2) & (lon_norm <= bb["lon_max"] + 2)
    near = np.sum(near_lat & near_lon)
    if near > 0:
        # Show the actual points
        mask = near_lat & near_lon
        lats_near = lat[mask]
        lons_near = lon_norm[mask]
        print(f"\n  {t['product_id'][:55]}: {near} points near OHRC")
        print(f"    lat range of nearby: {lats_near.min():.2f} to {lats_near.max():.2f}")
        print(f"    lon range of nearby: {lons_near.min():.2f} to {lons_near.max():.2f}")
        # How many are actually inside the OHRC bbox?
        in_bb = (lat >= bb["lat_min"]) & (lat <= bb["lat_max"]) & (lon_norm >= bb["lon_min"]) & (lon_norm <= bb["lon_max"])
        print(f"    inside OHRC bbox: {np.sum(in_bb)}")
