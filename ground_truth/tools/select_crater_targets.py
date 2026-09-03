import pandas as pd
from pathlib import Path


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_CSV = (
    PROJECT_ROOT
    / "ground_truth"
    / "manifests"
    / "crater_targets.csv"
)

OUTPUT_CSV = (
    PROJECT_ROOT
    / "ground_truth"
    / "manifests"
    / "selected_crater_targets.csv"
)


# ============================================================
# Selection settings
# ============================================================

MIN_DIAMETER_KM = 2.0

# Maximum targets from one OHRC scene
MAX_PER_OHRC = 2

# Overall maximum
MAX_TARGETS = 30


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)
    print("Selecting crater targets")
    print("=" * 60)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    print("\nLoading crater targets...")

    df = pd.read_csv(INPUT_CSV)

    print(
        f"Input combinations: {len(df):,}"
    )

    # --------------------------------------------------------
    # Remove invalid rows
    # --------------------------------------------------------

    required_columns = [
        "crater_id",
        "crater_latitude",
        "crater_longitude",
        "crater_diameter_km",
        "ohrc_product",
        "tmc2_product",
    ]

    df = df.dropna(
        subset=required_columns
    ).copy()

    # --------------------------------------------------------
    # Diameter filter
    # --------------------------------------------------------

    df = df[
        df["crater_diameter_km"]
        >= MIN_DIAMETER_KM
    ].copy()

    print(
        f"After diameter filter "
        f"(>= {MIN_DIAMETER_KM} km): "
        f"{len(df):,}"
    )

    # --------------------------------------------------------
    # Remove exact duplicates
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "crater_id",
            "ohrc_product",
            "tmc2_product",
        ]
    )

    # --------------------------------------------------------
    # Sort by crater size
    # --------------------------------------------------------

    df = df.sort_values(
        by="crater_diameter_km",
        ascending=False,
    )

    # ========================================================
    # Selection
    # ========================================================

    selected = []

    # Track how many targets each OHRC has
    ohrc_counts = {}

    # Track craters already selected
    selected_craters = set()

    # Track exact image combinations
    selected_combinations = set()

    # --------------------------------------------------------
    # Pass 1:
    # Prefer different craters and spread across OHRC scenes.
    # --------------------------------------------------------

    for _, row in df.iterrows():

        ohrc = row["ohrc_product"]
        tmc2 = row["tmc2_product"]
        crater = row["crater_id"]

        combination = (
            ohrc,
            tmc2,
            crater,
        )

        # Already selected exact combination
        if combination in selected_combinations:
            continue

        # Maximum targets per OHRC
        if ohrc_counts.get(ohrc, 0) >= MAX_PER_OHRC:
            continue

        # Prefer different craters
        if crater in selected_craters:
            continue

        selected.append(row)

        selected_combinations.add(
            combination
        )

        selected_craters.add(
            crater
        )

        ohrc_counts[ohrc] = (
            ohrc_counts.get(ohrc, 0) + 1
        )

        if len(selected) >= MAX_TARGETS:
            break

    # --------------------------------------------------------
    # Pass 2:
    # If we don't have enough targets, allow a crater to
    # appear again in a different image pair.
    # --------------------------------------------------------

    if len(selected) < MAX_TARGETS:

        for _, row in df.iterrows():

            if len(selected) >= MAX_TARGETS:
                break

            ohrc = row["ohrc_product"]
            tmc2 = row["tmc2_product"]
            crater = row["crater_id"]

            combination = (
                ohrc,
                tmc2,
                crater,
            )

            if combination in selected_combinations:
                continue

            if ohrc_counts.get(ohrc, 0) >= MAX_PER_OHRC:
                continue

            selected.append(row)

            selected_combinations.add(
                combination
            )

            ohrc_counts[ohrc] = (
                ohrc_counts.get(ohrc, 0) + 1
            )

    # --------------------------------------------------------
    # Convert to DataFrame
    # --------------------------------------------------------

    result = pd.DataFrame(selected)

    # --------------------------------------------------------
    # Add target IDs
    # --------------------------------------------------------

    result.insert(
        0,
        "target_id",
        [
            f"target_{i:03d}"
            for i in range(
                1,
                len(result) + 1,
            )
        ],
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    # ========================================================
    # Report
    # ========================================================

    print("\nSelected targets:")
    print("-" * 60)

    display_columns = [
        "target_id",
        "crater_id",
        "crater_latitude",
        "crater_longitude",
        "crater_diameter_km",
        "ohrc_product",
        "tmc2_product",
    ]

    print(
        result[
            display_columns
        ].to_string(index=False)
    )

    print("\n" + "=" * 60)

    print(
        f"Final targets selected: "
        f"{len(result)}"
    )

    print(
        f"Unique OHRC scenes represented: "
        f"{result['ohrc_product'].nunique()}"
    )

    print(
        f"Unique craters represented: "
        f"{result['crater_id'].nunique()}"
    )

    print("=" * 60)

    print("\nTargets per OHRC:")

    print(
        result[
            "ohrc_product"
        ].value_counts().to_string()
    )

    print("\nSaved to:")
    print(OUTPUT_CSV)


if __name__ == "__main__":
    main()