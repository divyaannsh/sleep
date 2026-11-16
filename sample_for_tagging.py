"""
sample_for_tagging.py  —  STEP 3a tool (prepare Fitzpatrick tagging sample)

Usage:
    PYTHONPATH=src .venv/bin/python3 sample_for_tagging.py

Pulls a stratified random sample (~50 per class, 300 total) from the combined
processed dataset (train + test), copies images into tagging_sample_output/,
generates an HTML review grid, and writes tagging_sample.csv with an empty
'fitzpatrick_tone' column for you to fill in manually (values 1-6, or "unsure").

This does NOT estimate skin tone automatically — that is a manual task.
"""

import os
import shutil
import pandas as pd

TRAIN_SPLIT  = "data/processed/train_split.csv"
TEST_SPLIT   = "data/processed/test_split.csv"
OUTPUT_DIR   = "tagging_sample_output"
SAMPLE_CSV   = "tagging_sample.csv"
N_PER_CLASS  = 50

CLASSES = ["acne", "eczema", "psoriasis", "fungal_infection", "rosacea", "none_of_these"]


def make_html(rows, output_dir):
    cards = ""
    for r in rows:
        cards += f"""
        <div class="card">
          <img src="{r['dest_filename']}" alt="{r['dest_filename']}">
          <p><b>{r['mapped_label']}</b></p>
          <p><code>{r['source_dataset']}</code></p>
          <p style="color:#aaa;font-size:0.68rem">{r['dest_filename']}</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>Fitzpatrick Tagging Sample</title>
  <style>
    body {{ font-family: sans-serif; background: #111; color: #eee; padding: 1rem; }}
    h1   {{ color: #4af; }}
    .grid {{ display: flex; flex-wrap: wrap; gap: 12px; }}
    .card {{ background: #222; border: 1px solid #444; border-radius: 6px;
              padding: 8px; width: 220px; text-align: center; }}
    .card img {{ width: 200px; height: 200px; object-fit: cover; border-radius: 4px; }}
    .card p   {{ font-size: 0.72rem; margin: 4px 0; word-break: break-all; }}
  </style>
</head>
<body>
  <h1>Fitzpatrick Tagging Sample ({len(rows)} images)</h1>
  <p>For each image, open <b>tagging_sample.csv</b> and fill in the
     <b>fitzpatrick_tone</b> column with a value from 1–6 (or "unsure").<br>
     Fitzpatrick scale: 1–2 = very light/light, 3–4 = medium/olive,
     5–6 = brown/dark.</p>
  <div class="grid">{cards}
  </div>
</body>
</html>"""
    out_path = os.path.join(output_dir, "tagging_review.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"HTML review grid saved to {out_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load and combine both splits
    dfs = []
    for path in [TRAIN_SPLIT, TEST_SPLIT]:
        if os.path.exists(path):
            dfs.append(pd.read_csv(path))
        else:
            print(f"[WARN] {path} not found — skipping.")
    if not dfs:
        print("[ERROR] No split CSVs found.")
        return

    combined = pd.concat(dfs, ignore_index=True)
    print(f"Combined dataset: {len(combined)} rows across both splits.")

    # Stratified sample: N_PER_CLASS per class
    sampled_rows = []
    for cls in CLASSES:
        subset = combined[combined["mapped_label"] == cls]
        n = min(N_PER_CLASS, len(subset))
        sample = subset.sample(n=n, random_state=42)
        print(f"  {cls}: sampled {n} / {len(subset)} available")
        sampled_rows.append(sample)

    sample_df = pd.concat(sampled_rows, ignore_index=True).sample(frac=1, random_state=42)
    print(f"\nTotal sampled: {len(sample_df)} images")

    # Copy images and build record list
    records = []
    for _, row in sample_df.iterrows():
        src = row["image_path"]
        if not os.path.exists(src):
            continue
        dataset  = row.get("dataset", "unknown")
        cls      = row["mapped_label"]
        ext      = os.path.splitext(src)[1]
        base     = os.path.splitext(os.path.basename(src))[0]
        dest_name = f"{cls}__{dataset}__{base}{ext}"
        dest_path = os.path.join(OUTPUT_DIR, dest_name)
        shutil.copy2(src, dest_path)

        records.append({
            "image_path":      src,
            "dest_filename":   dest_name,
            "mapped_label":    cls,
            "source_dataset":  dataset,
            "fitzpatrick_tone": "",   # ← fill this in manually
        })

    print(f"Copied {len(records)} images to {OUTPUT_DIR}/")

    # Write tagging CSV
    tag_df = pd.DataFrame(records)[
        ["image_path", "dest_filename", "mapped_label", "source_dataset", "fitzpatrick_tone"]
    ]
    tag_df.to_csv(SAMPLE_CSV, index=False)
    print(f"Tagging CSV (empty tone column) saved to {SAMPLE_CSV}")

    # Write HTML grid
    make_html(records, OUTPUT_DIR)
    print(f"\nNext step: open {OUTPUT_DIR}/tagging_review.html, fill in")
    print(f"{SAMPLE_CSV} 'fitzpatrick_tone' column, then run apply_tagging_sample.py")


if __name__ == "__main__":
    main()
