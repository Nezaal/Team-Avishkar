import pandas as pd
from pathlib import Path


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CRATER_CSV = (
    PROJECT_ROOT
    / "dataset"
    / "lunar_crater_database_robbins_2018"
    / "lunar_crater_database_robbins_2018_bundle"
    / "data"
    / "lunar_crater_database_robbins_2018.csv"
)

OHRC_CSV = (
    PROJECT_ROOT
    / "ground_truth"
    / "sources"
    / "coordinates_ohrc_iit.csv"
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
    / "crater_targets.csv"
)


# ============================================================
# Settings
# ============================================================

# Robbins DIAM_CIRC_IMG is treated as kilometres.
# 1 km = 1000 m.
MIN_DIAMETER_KM = 1.0


# ============================================================
# Longitude utilities
# ============================================================

def normalize_longitude(lon):
    """
    Convert longitude to [0, 360).
    """

    return lon % 360.0


# ============================================================
# Footprint handling
# ============================================================

def get_footprint(row):
    """
    Get the bounding latitude/longitude box of an image.

    All longitudes are converted to [0, 360).
    """

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

    latitudes = [
        float(x) for x in latitudes
        if pd.notna(x)
    ]

    longitudes = [
        normalize_longitude(float(x))
        for x in longitudes
        if pd.notna(x)
    ]

    if len(latitudes) < 4 or len(longitudes) < 4:
        return None

    return {
        "lat_min": min(latitudes),
        "lat_max": max(latitudes),
        "lon_min": min(longitudes),
        "lon_max": max(longitudes),
    }


def point_inside_footprint(lat, lon, footprint):
    """
    Check whether a geographic point lies inside
    the image bounding box.
    """

    lon = normalize_longitude(lon)

    return (
        footprint["lat_min"]
        <= lat
        <= footprint["lat_max"]
        and
        footprint["lon_min"]
        <= lon
        <= footprint["lon_max"]
    )


def footprints_overlap(a, b):
    """
    Check whether two image bounding boxes overlap.
    """

    lat_overlap = not (
        a["lat_max"] < b["lat_min"]
        or
        a["lat_min"] > b["lat_max"]
    )

    lon_overlap = not (
        a["lon_max"] < b["lon_min"]
        or
        a["lon_min"] > b["lon_max"]
    )

    return lat_overlap and lon_overlap


# ============================================================
# Load Robbins crater database
# ============================================================

def load_craters():

    print("Loading Robbins crater database...")

    columns = [
        "CRATER_ID",
        "LAT_CIRC_IMG",
        "LON_CIRC_IMG",
        "DIAM_CIRC_IMG",
    ]

    df = pd.read_csv(
        CRATER_CSV,
        usecols=columns,
    )

    df = df.dropna(subset=columns)

    # Diameter is in kilometres.
    df = df[
        df["DIAM_CIRC_IMG"] >= MIN_DIAMETER_KM
    ].copy()

    df["LON_NORMALIZED"] = (
        df["LON_CIRC_IMG"]
        .apply(normalize_longitude)
    )

    print(
        f"Crater records loaded: {len(df):,}"
    )

    return df


# ============================================================
# Load image catalogs
# ============================================================

def load_catalog(path, name):

    print(f"Loading {name} catalog...")

    df = pd.read_csv(path)

    print(
        f"{name} products: {len(df):,}"
    )

    return df


# ============================================================
# Find TMC-2 scenes overlapping OHRC
# ============================================================

def find_tmc2_candidates(ohrc_footprint, tmc2):

    candidates = []

    for _, row in tmc2.iterrows():

        tmc_footprint = get_footprint(row)

        if tmc_footprint is None:
            continue

        if footprints_overlap(
            ohrc_footprint,
            tmc_footprint,
        ):
            candidates.append(
                (row, tmc_footprint)
            )

    return candidates


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)
    print("Finding lunar crater targets")
    print("=" * 60)

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    craters = load_craters()

    ohrc = load_catalog(
        OHRC_CSV,
        "OHRC",
    )

    tmc2 = load_catalog(
        TMC2_CSV,
        "TMC-2",
    )

    results = []

    print()
    print("Searching OHRC scenes...")
    print()

    # ========================================================
    # Process every OHRC scene
    # ========================================================

    for ohrc_index, ohrc_row in ohrc.iterrows():

        ohrc_name = ohrc_row["name"]

        ohrc_footprint = get_footprint(
            ohrc_row
        )

        if ohrc_footprint is None:
            continue

        # ----------------------------------------------------
        # Find TMC-2 scenes overlapping this OHRC scene
        # ----------------------------------------------------

        tmc_candidates = find_tmc2_candidates(
            ohrc_footprint,
            tmc2,
        )

        if not tmc_candidates:
            continue

        # ----------------------------------------------------
        # First filter crater database by latitude.
        #
        # This avoids checking 1.3M craters individually.
        # ----------------------------------------------------

        crater_candidates = craters[
            (
                craters["LAT_CIRC_IMG"]
                >= ohrc_footprint["lat_min"]
            )
            &
            (
                craters["LAT_CIRC_IMG"]
                <= ohrc_footprint["lat_max"]
            )
        ]

        crater_count = 0

        # ----------------------------------------------------
        # Check every crater against OHRC
        # ----------------------------------------------------

        for _, crater in crater_candidates.iterrows():

            crater_lat = float(
                crater["LAT_CIRC_IMG"]
            )

            crater_lon = float(
                crater["LON_NORMALIZED"]
            )

            # Crater must be inside OHRC.
            if not point_inside_footprint(
                crater_lat,
                crater_lon,
                ohrc_footprint,
            ):
                continue

            # ------------------------------------------------
            # Now check the crater against TMC-2 scenes.
            # ------------------------------------------------

            for tmc_row, tmc_footprint in tmc_candidates:

                if not point_inside_footprint(
                    crater_lat,
                    crater_lon,
                    tmc_footprint,
                ):
                    continue

                results.append({
                    "crater_id": crater["CRATER_ID"],

                    "crater_latitude": crater_lat,

                    "crater_longitude": crater_lon,

                    "crater_diameter_km":
                        float(
                            crater["DIAM_CIRC_IMG"]
                        ),

                    "ohrc_product":
                        ohrc_name,

                    "tmc2_product":
                        tmc_row["name"],
                })

                crater_count += 1

        print(
            f"OHRC {ohrc_index + 1}/{len(ohrc)}: "
            f"{ohrc_name} → "
            f"{len(tmc_candidates)} TMC-2 candidates → "
            f"{crater_count} crater matches"
        )

    # ========================================================
    # Save results
    # ========================================================

    result_df = pd.DataFrame(results)

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_df.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    print()
    print("=" * 60)
    print(
        f"Crater/image combinations found: "
        f"{len(result_df):,}"
    )
    print("=" * 60)

    print()
    print("Saved to:")
    print(OUTPUT_CSV)

    if not result_df.empty:

        print()
        print(
            result_df.head(20).to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()