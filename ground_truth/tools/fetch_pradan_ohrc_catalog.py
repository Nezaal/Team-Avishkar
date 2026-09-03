from pathlib import Path
from playwright.sync_api import sync_playwright
import json

WFS_URL = "https://chmapbrowse.issdc.gov.in/server/wfs"

PARAMS = {
    "service": "wfs",
    "version": "2.0.0",
    "request": "GetFeature",
    "outputFormat": "application/json",
    "cql_filter": "(PRODUCT_ID LIKE '%ohr%') AND (BBOX(the_geom,40,-65,45,-60))",
    "typeName": (
        "moon:ins:ch2_ohr_cal,"
        "moon:ins:np:ch2_ohr_cal_np,"
        "moon:ins:sp:ch2_ohr_cal_sp"
    ),
}

STATE_FILE = Path("ground_truth") / "pradan_session.json"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        page = context.new_page()

        # Safely handle JavaScript dialogs
        def handle_dialog(dialog):
            print(f"Browser dialog: {dialog.message}")
            try:
                dialog.accept()
            except Exception:
                pass

        page.on("dialog", handle_dialog)

        print("Opening PRADAN...")

        page.goto(
            "https://chmapbrowse.issdc.gov.in/MapBrowse/",
            wait_until="domcontentloaded"
        )

        print()
        print("Log into ISSDC in the browser if required.")
        input("Press ENTER after you are logged in... ")

        # Save authenticated browser session
        context.storage_state(path=STATE_FILE)

        print("Authenticated session saved.")

        # Use the authenticated browser context to query WFS
        response = context.request.get(
            WFS_URL,
            params=PARAMS
        )

        print("Status:", response.status)
        print("Content-Type:", response.headers.get("content-type"))

        text = response.text()

        print("Response preview:")
        print(text[:500])

        content_type = response.headers.get("content-type", "").lower()

        if "application/json" not in content_type:
            print("\nERROR: WFS did not return JSON.")
            browser.close()
            return

        data = json.loads(text)

        features = data.get("features", [])

        print(f"\nOHRC products found: {len(features)}")

        for feature in features[:10]:
            props = feature.get("properties", {})
            print(props.get("PRODUCT_ID"))

        browser.close()


if __name__ == "__main__":
    main()