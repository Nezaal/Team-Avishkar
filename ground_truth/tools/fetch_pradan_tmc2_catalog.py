"""
Fetch the real, downloadable TMC-2 PRODUCT_IDs from the PRADAN
WFS service.

Why this exists
---------------
download_pradan_products.py uses `tmc2_product` IDs that come from
the IIT catalog's `name` column (e.g. ch2_tmc_ncn_..._g_grd_d18).
Those `_g_grd` names describe a georeferenced grid footprint and are
NOT the image product IDs PRADAN accepts for download -- which is why
pathConstructor returns HTTP 404 for them.

OHRC products happen to download fine because the IIT OHRC `name`
column (ch2_ohr_ncp_..._d_img_d18) IS the PRADAN PRODUCT_ID.

This tool queries PRADAN's WFS GetFeature endpoint for the TMC-2
layers to enumerate the real PRODUCT_IDs, so the target CSV can be
regenerated with IDs that actually download.

Requires an authenticated browser session (ISSDC login) in the same
way fetch_pradan_ohrc_catalog.py does.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json

WFS_URL = "https://chmapbrowse.issdc.gov.in/server/wfs"

BASE_PARAMS = {
    "service": "wfs",
    "version": "2.0.0",
    "request": "GetFeature",
    "outputFormat": "application/json",
}

# Candidate TMC-2 WFS layers. Mirrors the OHRC naming pattern
# (moon:ins:ch2_ohr_cal, moon:ins:np:ch2_ohr_cal_np,
#  moon:ins:sp:ch2_ohr_cal_sp). TMC-2 tiles are all near the
# south pole so the south-polar layer is the most likely one, but
# we probe all candidates and keep whatever returns features.
TMC_LAYERS = [
    "moon:ins:ch2_tmc_cal",
    "moon:ins:ch2_tmc_cal_sp",
    "moon:ins:sp:ch2_tmc_cal_sp",
    "moon:ins:np:ch2_tmc_cal_np",
    "moon:ins:ch2_tmc_ncn_cal",
]

# Bound the query to the south polar target region (broad box).
DEFAULT_BBOX = "40,-80,60,-50"

# Optional exact-ID probe for a single product (used to validate
# that a known name maps to a real PRODUCT_ID).
PROBE_LIKE = "ch2_tmc_ncn_20220112T1458093645_g_grd_d18"

STATE_FILE = Path("ground_truth") / "pradan_session.json"

OUTPUT_FILE = Path("ground_truth") / "manifests" / "tmc2_product_ids.json"


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)
    print("Fetch TMC-2 PRODUCT_IDs from PRADAN WFS")
    print("=" * 60)

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        page = context.new_page()

        def handle_dialog(dialog):
            print(f"Browser dialog: {dialog.message}")
            try:
                dialog.accept()
            except Exception:
                pass

        page.on("dialog", handle_dialog)

        print("\nOpening PRADAN...")

        page.goto(
            "https://chmapbrowse.issdc.gov.in/MapBrowse/",
            wait_until="domcontentloaded"
        )

        print("Log into ISSDC in the browser if required.")
        input("Press ENTER after you are logged in... ")

        # Save authenticated browser session
        context.storage_state(path=str(STATE_FILE))
        print("\nAuthenticated session saved.")

        all_features = []

        for layer in TMC_LAYERS:

            params = dict(BASE_PARAMS)
            params["typeName"] = layer
            params["cql_filter"] = (
                f"(PRODUCT_ID LIKE '%tmc%') AND "
                f"(BBOX(the_geom,{DEFAULT_BBOX}))"
            )

            print(f"\nQuerying layer: {layer}")

            try:
                response = context.request.get(
                    WFS_URL,
                    params=params
                )
            except Exception as e:
                print(f"  [ERR] request: {e}")
                continue

            print(f"  Status: {response.status}")
            print(
                "  Content-Type: "
                f"{response.headers.get('content-type')}"
            )

            text = response.text()

            content_type = (
                response.headers
                .get("content-type", "")
                .lower()
            )

            if "application/json" not in content_type:
                print("  [SKIP] not JSON (probably login HTML)")
                continue

            try:
                data = json.loads(text)
            except Exception as e:
                print(f"  [ERR] JSON parse: {e}")
                continue

            features = data.get("features", [])

            print(f"  Features: {len(features)}")

            for feature in features:
                props = feature.get("properties", {})
                pid = props.get("PRODUCT_ID")
                if pid:
                    all_features.append(props)

        # ------------------------------------------------------
        # De-duplicate
        # ------------------------------------------------------

        seen = {}
        for props in all_features:
            pid = props.get("PRODUCT_ID")
            if pid and pid not in seen:
                seen[pid] = props

        print("\n" + "=" * 60)
        print(f"Unique TMC-2 PRODUCT_IDs found: {len(seen)}")
        print("=" * 60)

        for pid in sorted(seen.keys()):
            props = seen[pid]
            print(
                f"  {pid}  "
                f"(OBS_ST_TIME={props.get('OBS_ST_TIME')}, "
                f"BEGIN_TIME={props.get('BEGIN_TIME')})"
            )

        # ------------------------------------------------------
        # Probe: does a known IIT name appear as a real ID?
        # ------------------------------------------------------

        if PROBE_LIKE in seen:
            print(f"\n[MATCH] {PROBE_LIKE} found as a real PRODUCT_ID.")
        else:
            print(f"\n[NO MATCH] {PROBE_LIKE} NOT found among real IDs.")
            print("This confirms the IIT '_g_grd' name is not "
                  "a downloadable PRODUCT_ID.")

        # ------------------------------------------------------
        # Probe: compare against the target CSV TMC-2 IDs
        # ------------------------------------------------------

        try:
            import csv
            target_ids = set()
            targets_file = Path(
                "ground_truth/manifests/selected_crater_targets.csv"
            )
            with open(targets_file, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    t = (row.get("tmc2_product") or "").strip()
                    if t:
                        target_ids.add(t)

            print("\n" + "=" * 60)
            print("Target CSV TMC-2 IDs vs real WFS IDs")
            print("=" * 60)
            for tid in sorted(target_ids):
                status = "REAL" if tid in seen else "NOT-FOUND"
                print(f"  [{status}] {tid}")

        except Exception as e:
            print(f"\n[ERR] comparing target CSV: {e}")

        # ------------------------------------------------------
        # Save
        # ------------------------------------------------------

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {pid: props for pid, props in seen.items()},
                f,
                indent=2,
                default=str,
            )

        print(f"\nSaved real PRODUCT_IDs to: {OUTPUT_FILE}")

        browser.close()


if __name__ == "__main__":
    main()
