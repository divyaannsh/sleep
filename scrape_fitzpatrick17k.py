# scrape_fitzpatrick17k.py
# Downloads Fitzpatrick17k images from their source URLs (CSV only ships
# metadata + URLs, not bundled images). Expect partial success — many
# source URLs from this 2021 dataset are likely dead by now.

import os
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

CSV_PATH   = "data/raw/fitzpatrick17k/fitzpatrick17k.csv"
OUTPUT_DIR = "data/raw/fitzpatrick17k/images"
TIMEOUT    = 10
MAX_WORKERS = 8   # keep modest, don't hammer source sites

HEADERS = {
    "User-Agent": "Mozilla/5.0 (research dataset download; Fitzpatrick17k)"
}

def download_one(row):
    md5hash = str(row["md5hash"])
    url     = str(row["url"])
    out_path = os.path.join(OUTPUT_DIR, f"{md5hash}.jpg")

    if os.path.exists(out_path):
        return md5hash, "skipped_exists"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        ct = resp.headers.get("content-type", "")
        if resp.status_code == 200 and "image" in ct:
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            return md5hash, "ok"
        else:
            return md5hash, f"failed_status_{resp.status_code}"
    except requests.exceptions.RequestException as e:
        return md5hash, f"failed_{type(e).__name__}"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found at {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    print(f"Total rows in CSV: {len(df)}")

    # Only download rows that have a valid URL
    df = df[df["url"].notna() & (df["url"].astype(str).str.startswith("http"))]
    print(f"Rows with valid URLs: {len(df)}")

    results = {"ok": 0, "skipped_exists": 0, "failed": 0}
    failed_log = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(download_one, row): row["md5hash"]
            for _, row in df.iterrows()
        }
        completed = 0
        for future in as_completed(futures):
            md5hash, status = future.result()
            completed += 1
            if status == "ok":
                results["ok"] += 1
            elif status == "skipped_exists":
                results["skipped_exists"] += 1
            else:
                results["failed"] += 1
                failed_log.append((md5hash, status))

            if completed % 200 == 0:
                pct = (results["ok"] + results["skipped_exists"]) / completed * 100
                print(f"  Progress: {completed}/{len(df)} | "
                      f"ok={results['ok']}  skipped={results['skipped_exists']}  "
                      f"failed={results['failed']}  ({pct:.0f}% success so far)")

    print("\n================ DOWNLOAD SUMMARY ================")
    print(f"Total rows attempted:      {len(df)}")
    print(f"Successfully downloaded:   {results['ok']}")
    print(f"Already existed (skipped): {results['skipped_exists']}")
    print(f"Failed:                    {results['failed']}")
    total_good = results["ok"] + results["skipped_exists"]
    print(f"Success rate:              {total_good / len(df) * 100:.1f}%")
    print("==================================================")

    if failed_log:
        fail_df = pd.DataFrame(failed_log, columns=["md5hash", "reason"])
        fail_df.to_csv("data/raw/fitzpatrick17k/download_failures.csv", index=False)
        print(f"\nFailure log → data/raw/fitzpatrick17k/download_failures.csv")

if __name__ == "__main__":
    main()
