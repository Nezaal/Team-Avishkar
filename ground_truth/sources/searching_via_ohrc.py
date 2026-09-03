import pandas as pd

csv_path = r"C:\Users\Nezaal\projects\sih2026\dataset\ch2_ohr_ncp_20211228T2209123959_d_img_d18\geometry\calibrated\20211228\ch2_ohr_ncp_20211228T2209123959_g_grd_d18.csv"

df = pd.read_csv(csv_path)

print("Rows:", len(df))
print("Columns:", df.columns.tolist())

print("\nLatitude range:")
print(df["Latitude"].min(), "to", df["Latitude"].max())

print("\nLongitude range:")
print(df["Longitude"].min(), "to", df["Longitude"].max())

print("\nPixel range:")
print(df["Pixel"].min(), "to", df["Pixel"].max())

print("\nScan range:")
print(df["Scan"].min(), "to", df["Scan"].max())