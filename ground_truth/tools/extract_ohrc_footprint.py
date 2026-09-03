import pandas as pd

csv_path = r"C:\Users\Nezaal\projects\sih2026\dataset\ch2_ohr_ncp_20211228T2209123959_d_img_d18\geometry\calibrated\20211228\ch2_ohr_ncp_20211228T2209123959_g_grd_d18.csv"

df = pd.read_csv(csv_path)

# Convert longitudes from [0, 360] to [-180, 180]
df["Longitude_normalized"] = (
    (df["Longitude"] + 180) % 360
) - 180

min_pixel = df["Pixel"].min()
max_pixel = df["Pixel"].max()
min_scan = df["Scan"].min()
max_scan = df["Scan"].max()

corners = {
    "top_left": (min_pixel, min_scan),
    "top_right": (max_pixel, min_scan),
    "bottom_left": (min_pixel, max_scan),
    "bottom_right": (max_pixel, max_scan),
}

for name, (pixel, scan) in corners.items():
    row = df[
        (df["Pixel"] == pixel) &
        (df["Scan"] == scan)
    ]

    if not row.empty:
        r = row.iloc[0]

        print(
            f"{name}: "
            f"Lon={r['Longitude']:.6f}, "
            f"Normalized Lon={r['Longitude_normalized']:.6f}, "
            f"Lat={r['Latitude']:.6f}"
        )