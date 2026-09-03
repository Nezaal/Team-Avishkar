from pathlib import Path
import csv
import json
import shutil
import subprocess
import sys
import time

import requests
from playwright.sync_api import sync_playwright


# ============================================================
# CONFIG
# ============================================================

BASE_URL = "https://chmapbrowse.issdc.gov.in"
MAP_URL = f"{BASE_URL}/MapBrowse/"
PATH_CONSTRUCTOR = f"{BASE_URL}/server/pathConstructor"
DOWNLOAD_URL = f"{BASE_URL}/server/bundleZipDownload"

TARGETS_FILE = Path(
    "ground_truth/manifests/selected_crater_targets.csv"
)

DOWNLOAD_DIR = Path(
    "dataset/pradan_downloads"
)

# Per-sensor destination folders. OHRC and TMC-2 products are
# kept in separate subdirectories.
OHRC_DIR = DOWNLOAD_DIR / "ohrc"
TMC2_DIR = DOWNLOAD_DIR / "tmc-2"

# Persistent browser profile.
# This keeps the ISSDC login between script executions.
BROWSER_PROFILE = Path(
    "ground_truth/pradan_browser"
)


# ============================================================
# PROFILE PROCESS CLEANUP
# ============================================================

def _kill_profile_processes(profile_path):
    """
    Terminate any Chromium processes still holding the
    persistent browser profile directory.

    On Windows a profile directory is locked until every
    child process has exited. Deleting a live profile and
    immediately relaunching Playwright therefore fails with
    "Connection closed while reading from the driver".

    wmic is removed from modern Windows, so enumerate and
    stop processes via PowerShell CIM (Get-CimInstance).
    """

    profile = Path(profile_path).resolve()

    drive_less = str(profile).replace(":", "", 1)

    print(
        "Releasing browser profile processes..."
    )

    ps_script = (
        "$targets = Get-CimInstance Win32_Process "
        "-Filter \"Name = 'chrome.exe'\" | "
        "Where-Object { $_.CommandLine -match '"
        + drive_less.replace("\\", "\\\\")
        + "' }; "
        "$targets | ForEach-Object { "
        "Stop-Process -Id $_.ProcessId -Force "
        "-ErrorAction SilentlyContinue }; "
        "$targets.Count"
    )

    try:

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                ps_script
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        count = result.stdout.strip()

    except Exception as e:

        print(
            "[WARN] Could not query browser processes:",
            e
        )

        return

    if count and count.isdigit() and int(count) > 0:

        print(
            f"Stopped {count} stale browser process(es)."
        )

        # Allow the OS to release the locks.
        time.sleep(2)

    else:

        print("No stale browser processes found.")


# ============================================================
# LOAD PRODUCTS
# ============================================================

def load_products():

    products = set()

    with open(
        TARGETS_FILE,
        newline="",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            ohr = row.get(
                "ohrc_product",
                ""
            ).strip()

            tmc = row.get(
                "tmc2_product",
                ""
            ).strip()

            if ohr:
                products.add(ohr)

            if tmc:
                products.add(tmc)

    return sorted(products)


# ============================================================
# DESTINATION FOLDER FOR A PRODUCT
# ============================================================

def product_dir(product_id):
    """
    Return the destination folder for a product ID.

    OHRC products (ch2_ohr_*) go to <DOWNLOAD_DIR>/ohrc and
    TMC-2 products (ch2_tmc_*) go to <DOWNLOAD_DIR>/tmc-2, so
    the two sensors' files never mix.
    """

    if product_id.startswith("ch2_ohr_"):
        return OHRC_DIR

    if product_id.startswith("ch2_tmc_"):
        return TMC2_DIR

    return DOWNLOAD_DIR


# ============================================================
# START BROWSER
# ============================================================

def start_browser(p):

    fresh_login = "--fresh-login" in sys.argv

    if fresh_login:
        print("\nRemoving old PRADAN browser profile...")
        shutil.rmtree(
            BROWSER_PROFILE,
            ignore_errors=True
        )

    BROWSER_PROFILE.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\nStarting PRADAN browser...")

    # Persistent profile keeps the ISSDC login between runs.
    # A fresh profile is created when --fresh-login is supplied.
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(BROWSER_PROFILE),
        headless=False,
        accept_downloads=True,
        args=[
            "--disable-popup-blocking",
            "--disable-features=AutomationControlled"
        ]
    )

    browser = context.browser

    page = context.new_page()

    # Auto-dismiss any JavaScript dialogs. PRADAN opens
    # popups/dialogs that can otherwise surface as an
    # unhandled Playwright ProtocolError during shutdown
    # ("No dialog is showing") and crash the whole process.
    #
    # dialog.dismiss() itself can raise the same protocol
    # error when the dialog has already been closed by the
    # page, so the handler must never let that propagate.
    def _silent_dismiss(dialog):
        try:
            dialog.dismiss()
        except Exception:
            pass

    page.on(
        "dialog",
        _silent_dismiss
    )

    print("\nOpening PRADAN...")

    try:
        page.goto(
            MAP_URL,
            wait_until="domcontentloaded",
            timeout=120000
        )
    except Exception as e:
        print(
            "[WARN] PRADAN page navigation:",
            e
        )

    print()
    print(
        "Log into ISSDC in the browser."
    )
    print(
        "Handle any PRADAN popup/dialog manually."
    )

    input(
        "Press ENTER when PRADAN is ready... "
    )

    print(
        "\nPRADAN browser session ready."
    )

    return browser, context

# ============================================================
# CREATE REQUESTS SESSION FROM BROWSER COOKIES
# ============================================================

def create_requests_session(context):

    session = requests.Session()

    for cookie in context.cookies():

        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=cookie.get(
                "domain"
            ),
            path=cookie.get(
                "path",
                "/"
            )
        )

    session.headers.update({

        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/152.0.0.0 "
            "Safari/537.36"
        ),

        "Accept": "*/*",

        "Referer": MAP_URL
    })

    return session


# ============================================================
# DOWNLOAD ONE PRODUCT
# ============================================================

def download_product(
    context,
    session,
    product_id
):

    dest_dir = product_dir(product_id)

    output_file = (
        dest_dir /
        f"{product_id}.zip"
    )

    temp_file = (
        dest_dir /
        f"{product_id}.zip.part"
    )

    # --------------------------------------------------------
    # 1. Ask PRADAN for download path
    # --------------------------------------------------------

    print(
        "\nRequesting download path..."
    )

    payload = json.dumps([
        {
            "productId": product_id
        }
    ])

    response = session.post(
        PATH_CONSTRUCTOR,
        data=payload,
        headers={
            "Content-Type":
                "application/json",
            "Accept":
                "application/json",
            "Referer":
                MAP_URL
        },
        timeout=60
    )

    print(
        "pathConstructor:",
        response.status_code
    )

    print(
        "Response:",
        response.text[:500]
    )

    # --------------------------------------------------------
    # Session/auth problems (401/403) mean the login expired
    # and the whole session must be refreshed.
    #
    # A 404 means PRADAN does not know this product ID (the ID
    # is missing or fabricated) -- NOT an auth problem. Treat
    # it as a per-product failure so it does not trigger a
    # heavyweight browser relaunch for every bad ID.
    # --------------------------------------------------------

    if response.status_code in (
        401,
        403
    ):

        raise RuntimeError(
            f"SESSION_EXPIRED:{response.status_code}"
        )

    if response.status_code != 200:

        raise RuntimeError(
            "pathConstructor failed: "
            f"HTTP {response.status_code}"
        )

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        data = response.json()

    except Exception:

        # HTML login page means session expired.
        if (
            "text/html"
            in response.headers.get(
                "content-type",
                ""
            ).lower()
        ):

            raise RuntimeError(
                "SESSION_EXPIRED:HTML_LOGIN"
            )

        raise RuntimeError(
            "pathConstructor did not "
            "return valid JSON."
        )

    # --------------------------------------------------------
    # PRADAN returns either:
    #
    # {"redirect": "..."}
    #
    # or:
    #
    # [{"redirect": "..."}]
    # --------------------------------------------------------

    if isinstance(data, dict):

        redirect_url = data.get(
            "redirect"
        )

    elif (
        isinstance(data, list)
        and len(data) > 0
        and isinstance(data[0], dict)
    ):

        redirect_url = data[0].get(
            "redirect"
        )

    else:

        redirect_url = None

    if not redirect_url:

        raise RuntimeError(
            f"No redirect returned: {data}"
        )

    print(
        "\nRedirect:",
        redirect_url
    )

    # ========================================================
    # 2. STREAM ZIP TO DISK
    # ========================================================

    print(
        "\nDownloading product..."
    )

    print(
        "Streaming directly to disk."
    )

    # Delete stale partial file.
    temp_file.unlink(
        missing_ok=True
    )

    with session.get(
        redirect_url,
        headers={
            "Accept": "*/*",
            "Referer": MAP_URL
        },
        stream=True,
        timeout=(30, 900)
    ) as download_response:

        print(
            "Download response:",
            download_response.status_code
        )

        print(
            "Content-Type:",
            download_response.headers.get(
                "content-type"
            )
        )

        print(
            "Content-Length:",
            download_response.headers.get(
                "content-length"
            )
        )

        print(
            "Content-Disposition:",
            download_response.headers.get(
                "content-disposition"
            )
        )

        if download_response.status_code in (
            401,
            403
        ):

            raise RuntimeError(
                "SESSION_EXPIRED:"
                f"DOWNLOAD_{download_response.status_code}"
            )

        if download_response.status_code != 200:

            raise RuntimeError(
                "Download failed: "
                f"HTTP {download_response.status_code}"
            )

        content_type = (
            download_response.headers.get(
                "content-type",
                ""
            ).lower()
        )

        if "text/html" in content_type:

            raise RuntimeError(
                "SESSION_EXPIRED:"
                "DOWNLOAD_HTML"
            )

        total = int(
            download_response.headers.get(
                "content-length",
                0
            )
        )

        downloaded = 0

        with open(
            temp_file,
            "wb"
        ) as f:

            for chunk in download_response.iter_content(
                chunk_size=1024 * 1024
            ):

                if not chunk:
                    continue

                f.write(chunk)

                downloaded += len(chunk)

                if total:

                    percent = (
                        downloaded /
                        total *
                        100
                    )

                    print(
                        f"\rProgress: "
                        f"{percent:6.2f}% "
                        f"("
                        f"{downloaded / 1024 / 1024:.1f}"
                        f" MB)",
                        end="",
                        flush=True
                    )

                else:

                    print(
                        f"\rDownloaded: "
                        f"{downloaded / 1024 / 1024:.1f}"
                        f" MB",
                        end="",
                        flush=True
                    )

    print()

    # ========================================================
    # 3. VALIDATE ZIP
    # ========================================================

    if not temp_file.exists():

        raise RuntimeError(
            "Temporary download file "
            "was not created."
        )

    file_size = (
        temp_file.stat().st_size
    )

    if file_size < 4:

        temp_file.unlink(
            missing_ok=True
        )

        raise RuntimeError(
            "Downloaded file is empty."
        )

    with open(
        temp_file,
        "rb"
    ) as f:

        signature = f.read(4)

    if signature != b"PK\x03\x04":

        temp_file.unlink(
            missing_ok=True
        )

        raise RuntimeError(
            "Downloaded response is "
            "not a valid ZIP file."
        )

    # --------------------------------------------------------
    # Only now mark the download complete.
    # --------------------------------------------------------

    temp_file.replace(
        output_file
    )

    size_mb = (
        file_size /
        (1024 * 1024)
    )

    print(
        "[OK] Saved:"
    )

    print(
        output_file
    )

    print(
        f"[OK] Size: {size_mb:.2f} MB"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )
    OHRC_DIR.mkdir(
        parents=True,
        exist_ok=True
    )
    TMC2_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    products = load_products()

    print("=" * 60)
    print("PRADAN Product Downloader")
    print("=" * 60)

    print(
        f"\nUnique products required: {len(products)}"
    )

    print(
        f"Download directory: {DOWNLOAD_DIR.resolve()}"
    )

    with sync_playwright() as p:

        browser = None
        context = None
        session = None

        successful = 0
        failed = 0

        try:

            # ================================================
            # INITIAL SESSION
            # ================================================

            browser, context = start_browser(p)

            session = create_requests_session(context)

            index = 0

            while index < len(products):

                product_id = products[index]

                print("\n" + "=" * 60)
                print(
                    f"Product {index + 1}/{len(products)}"
                )
                print("=" * 60)
                print(product_id)

                output_file = (
                    product_dir(product_id) /
                    f"{product_id}.zip"
                )

                # ============================================
                # SKIP ALREADY DOWNLOADED
                # ============================================

                if (
                    output_file.exists()
                    and output_file.stat().st_size > 0
                ):

                    size_mb = (
                        output_file.stat().st_size
                        / (1024 * 1024)
                    )

                    print(
                        f"[SKIP] Already downloaded "
                        f"({size_mb:.2f} MB)"
                    )

                    successful += 1
                    index += 1
                    continue

                # ============================================
                # DOWNLOAD
                # ============================================

                if session is None:

                    # Never continue a batch with a dead
                    # session: every download would otherwise
                    # fail with a confusing AttributeError.
                    print(
                        "\n[FATAL] No PRADAN session available "
                        "before product. Aborting remaining "
                        "products."
                    )

                    raise RuntimeError(
                        "PRADAN_SESSION_CREATION_FAILED"
                    )

                try:

                    download_product(
                        context,
                        session,
                        product_id
                    )

                    successful += 1
                    index += 1

                except RuntimeError as e:

                    error = str(e)

                    # ========================================
                    # SESSION EXPIRED
                    # ========================================

                    if error.startswith(
                        "SESSION_EXPIRED"
                    ):

                        print(
                            "\n[SESSION EXPIRED]"
                        )

                        print(
                            "Refreshing PRADAN session..."
                        )

                        # ------------------------------------
                        # Safely close old browser and fully
                        # release the persistent profile before
                        # deleting it. On Windows the profile
                        # directory is locked until every
                        # Chromium process has exited, otherwise
                        # the relaunch dies with
                        # "Connection closed while reading
                        # from the driver".
                        # ------------------------------------

                        try:
                            if browser:
                                browser.close()
                        except Exception:
                            pass

                        try:
                            if context:
                                context.close()
                        except Exception:
                            pass

                        # Give the OS a moment to release locks.
                        time.sleep(2)

                        # Kill any Chromium processes still
                        # holding the profile directory.
                        _kill_profile_processes(BROWSER_PROFILE)

                        context = None
                        browser = None
                        session = None

                        # ------------------------------------
                        # Remove old browser profile
                        # ------------------------------------

                        print(
                            "Removing expired browser profile..."
                        )

                        shutil.rmtree(
                            BROWSER_PROFILE,
                            ignore_errors=True
                        )

                        # ------------------------------------
                        # Start completely new session.
                        # Retry the relaunch a couple of times,
                        # since a transient driver hiccup should
                        # not cascade into a dead session for
                        # every remaining product.
                        # ------------------------------------

                        NEW_SESSION_RETRIES = 3

                        session_created = False

                        for attempt in range(1, NEW_SESSION_RETRIES + 1):

                            try:

                                browser, context = start_browser(p)

                                session = (
                                    create_requests_session(
                                        context
                                    )
                                )

                                print(
                                    "\nSession refreshed successfully."
                                )

                                session_created = True

                                break

                            except Exception as session_error:

                                print(
                                    f"\n[WARN] Could not create new "
                                    f"PRADAN session "
                                    f"(attempt {attempt}/"
                                    f"{NEW_SESSION_RETRIES}):"
                                )

                                print(session_error)

                                # Clean up before retry.
                                try:
                                    if browser:
                                        browser.close()
                                except Exception:
                                    pass

                                try:
                                    if context:
                                        context.close()
                                except Exception:
                                    pass

                                browser = None
                                context = None
                                session = None

                                time.sleep(3)

                        if not session_created:

                            # Without a live session every later
                            # product would just fail with a
                            # confusing AttributeError. Stop the
                            # batch instead.
                            print(
                                "\n[FATAL] Could not re-establish "
                                "PRADAN session after "
                                f"{NEW_SESSION_RETRIES} attempts. "
                                "Login manually, then rerun. "
                                "Remaining products aborted."
                            )

                            aborted = (
                                len(products) - index
                            )

                            print(
                                f"Aborted remaining: {aborted}"
                            )

                            raise RuntimeError(
                                "PRADAN_SESSION_CREATION_FAILED"
                            )

                        # ------------------------------------
                        # Retry SAME product
                        # ------------------------------------

                        print(
                            "\nRetrying product..."
                        )

                        try:

                            download_product(
                                context,
                                session,
                                product_id
                            )

                            successful += 1
                            index += 1

                            print(
                                "[OK] Product downloaded "
                                "after session refresh."
                            )

                        except Exception as retry_error:

                            failed += 1
                            index += 1

                            print(
                                "\n[ERROR] Retry failed:"
                            )

                            print(retry_error)

                    else:

                        failed += 1
                        index += 1

                        print(
                            "\n[ERROR]",
                            e
                        )

                except Exception as e:

                    failed += 1
                    index += 1

                    print(
                        "\n[ERROR]",
                        type(e).__name__,
                        e
                    )

                time.sleep(1)

        finally:

            # ================================================
            # SAFE BROWSER SHUTDOWN
            # ================================================

            if context:
                try:
                    context.close()
                except Exception:
                    pass

            # For persistent contexts, closing the context normally
            # closes its browser. Keep this guarded for disconnected
            # Chromium sessions.
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass

            # Ensure the persistent profile is fully released so a
            # subsequent run can relaunch cleanly. Otherwise the
            # profile directory stays locked by orphaned Chromium
            # processes and the next launch fails with
            # "Connection closed while reading from the driver".
            time.sleep(1)
            _kill_profile_processes(BROWSER_PROFILE)

        # ====================================================
        # FINAL SUMMARY
        # ====================================================

        print("\n" + "=" * 60)
        print("DOWNLOAD PROCESS FINISHED")
        print("=" * 60)

        print(f"Successful: {successful}")
        print(f"Failed:     {failed}")
        print(f"Total:      {len(products)}")

        print("\nDownload directory:")
        print(DOWNLOAD_DIR.resolve())

if __name__ == "__main__":

    main()