# 


import pandas as pd
from pathlib import Path


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OHRC_GEOMETRY = (
    PROJECT_ROOT
    / "dataset"
    / "ch2_ohr_ncp_20211228T2209123959_d_img_d18"
    / "geometry"
    / "calibrated"
    / "20211228"
    / "ch2_ohr_ncp_20211228T2209123959_g_grd_d18.csv"
)

TMC2_CSV = (
    PROJECT_ROOT
    / "ground_truth"
    / "sources"
    / "coordinates_tmc2_iit.csv"
)

OUTPUT_CSV = (
    PROJECT_ROOT
    / "ground_truth"
    / "manifests"
    / "tmc2_candidates.csv"
)


# ============================================================
# Longitude utilities
# ============================================================

def normalize_longitude(lon):
    """
    Convert longitude from [0, 360] or any equivalent representation
    into [-180, 180].
    """
    return ((lon + 180) % 360) - 180


def longitude_interval(lons):
    """
    Find the smaller longitude interval containing all longitudes.

    Handles scenes crossing the ±180° meridian.
    """

    lons = sorted(normalize_longitude(x) for x in lons)

    # Find the largest gap between consecutive points.
    gaps = []

    for i in range(len(lons) - 1):
        gaps.append((lons[i + 1] - lons[i], i))

    # Circular gap
    circular_gap = (lons[0] + 360) - lons[-1]
    gaps.append((circular_gap, len(lons) - 1))

    # Remove the largest gap.
    # The remaining section is the smallest containing interval.
    _, index = max(gaps)

    start = lons[(index + 1) % len(lons)]
    end = lons[index]

    return start, end


# ============================================================
# Load OHRC footprint
# ============================================================

def load_ohrc_footprint():

    print(f"Reading OHRC geometry:")
    print(OHRC_GEOMETRY)

    df = pd.read_csv(OHRC_GEOMETRY)

    required = ["Longitude", "Latitude"]

    for column in required:
        if column not in df.columns:
            raise ValueError(
                f"OHRC geometry is missing column: {column}"
            )

    df = df.dropna(subset=required)

    longitudes = df["Longitude"].tolist()

    lat_min = df["Latitude"].min()
    lat_max = df["Latitude"].max()

    lon_start, lon_end = longitude_interval(longitudes)

    print()
    print("OHRC footprint")
    print("-------------------------")
    print(f"Latitude : {lat_min:.6f} → {lat_max:.6f}")
    print(f"Longitude: {lon_start:.6f} → {lon_end:.6f}")

    return {
        "lat_min": lat_min,
        "lat_max": lat_max,
        "lon_start": lon_start,
        "lon_end": lon_end,
    }


# ============================================================
# Check latitude overlap
# ============================================================

def latitude_overlap(a_min, a_max, b_min, b_max):

    return (
        a_min <= b_max
        and
        b_min <= a_max
    )


# ============================================================
# Check longitude overlap
# ============================================================

def longitude_segments(start, end):
    """
    Convert a possibly antimeridian-crossing interval into
    one or two normal intervals.

    Example:

        170 → -170

    becomes:

        170 → 180
        -180 → -170
    """

    if start <= end:

        return [(start, end)]

    else:

        return [
            (start, 180),
            (-180, end),
        ]


def longitude_overlap(a_start, a_end, b_start, b_end):

    a_segments = longitude_segments(a_start, a_end)
    b_segments = longitude_segments(b_start, b_end)

    for a_min, a_max in a_segments:
        for b_min, b_max in b_segments:

            if (
                a_min <= b_max
                and
                b_min <= a_max
            ):
                return True

    return False


# ============================================================
# Build TMC-2 footprint
# ============================================================

def get_tmc2_footprint(row):

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

    latitudes = [x for x in latitudes if pd.notna(x)]
    longitudes = [x for x in longitudes if pd.notna(x)]

    if not latitudes or not longitudes:
        return None

    lat_min = min(latitudes)
    lat_max = max(latitudes)

    lon_start, lon_end = longitude_interval(longitudes)

    return {
        "lat_min": lat_min,
        "lat_max": lat_max,
        "lon_start": lon_start,
        "lon_end": lon_end,
    }


# ============================================================
# Find candidate TMC-2 products
# ============================================================

def find_candidates(ohrc):

    print()
    print(f"Reading TMC-2 catalog:")
    print(TMC2_CSV)

    tmc2 = pd.read_csv(TMC2_CSV)

    print(f"TMC-2 products: {len(tmc2)}")

    candidates = []

    for _, row in tmc2.iterrows():

        footprint = get_tmc2_footprint(row)

        if footprint is None:
            continue

        # First filter by latitude.
        if not latitude_overlap(
            ohrc["lat_min"],
            ohrc["lat_max"],
            footprint["lat_min"],
            footprint["lat_max"],
        ):
            continue

        # Then filter by longitude.
        if not longitude_overlap(
            ohrc["lon_start"],
            ohrc["lon_end"],
            footprint["lon_start"],
            footprint["lon_end"],
        ):
            continue

        candidates.append({
            "ohrc_product": (
                "ch2_ohr_ncp_20211228T2209123959_d_img_d18"
            ),
            "tmc2_product": row["name"],

            "tmc2_lat_min": footprint["lat_min"],
            "tmc2_lat_max": footprint["lat_max"],
            "tmc2_lon_start": footprint["lon_start"],
            "tmc2_lon_end": footprint["lon_end"],
        })

    return candidates


# ============================================================
# Main
# ============================================================

def main():

    ohrc = load_ohrc_footprint()

    candidates = find_candidates(ohrc)

    print()
    print("==============================")
    print(f"Candidate TMC-2 products: {len(candidates)}")
    print("==============================")

    if not candidates:
        print("No overlapping TMC-2 products found.")
        return

    result = pd.DataFrame(candidates)

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_CSV,
        index=False
    )

    print()
    print(f"Saved candidates to:")
    print(OUTPUT_CSV)

    print()
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()