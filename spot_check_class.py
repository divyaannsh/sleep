"""
spot_check_class.py  —  STEP 2 tool (manual review, not auto-judging)

Usage:
    PYTHONPATH=src .venv/bin/python3 spot_check_class.py --class_name psoriasis --n 30

Copies N random images for the given class from both train + test splits into
spot_check_output/<class_name>/ and generates a review.html grid so you can
visually inspect them in a browser.  Filenames include the source dataset so
you can tell which dataset a bad image came from.
"""

import os
import argparse
import shutil
import pandas as pd

TRAIN_SPLIT = "data/processed/train_split.csv"
TEST_SPLIT  = "data/processed/test_split.csv"
OUTPUT_ROOT = "spot_check_output"


def make_html(images_info, class_name, output_dir):
    """Generates a simple HTML grid with filename and source dataset labels."""
    rows = ""
    for info in images_info:
        fname  = info["dest_filename"]
        source = info["source_dataset"]
        split  = info["split"]
        rows += f"""
        <div class="card">
          <img src="{fname}" alt="{fname}">
          <p><b>{fname}</b></p>
          <p>Dataset: <code>{source}</code> | Split: {split}</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
  <title>Spot-check: {class_name}</title>
  <style>
    body {{ font-family: sans-serif; background: #111; color: #eee; padding: 1rem; }}
    h1   {{ color: #f4a; }}
    .grid {{ display: flex; flex-wrap: wrap; gap: 12px; }}
    .card {{ background: #222; border: 1px solid #444; border-radius: 6px;
              padding: 8px; width: 220px; text-align: center; }}
    .card img {{ width: 200px; height: 200px; object-fit: cover; border-radius: 4px; }}
    .card p   {{ font-size: 0.72rem; margin: 4px 0; word-break: break-all; }}
  </style>
</head>
<body>
  <h1>Spot-check: {class_name} ({len(images_info)} images)</h1>
  <p>Manually review each image and report back how many look mislabeled or
     low-quality before proceeding to model fixes.</p>
  <div class="grid">{rows}
  </div>
</body>
</html>"""
    out_path = os.path.join(output_dir, "review.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"HTML review grid saved to {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--class_name", default="psoriasis",
                        help="mapped_label value to spot-check")
    parser.add_argument("--n", type=int, default=30,
                        help="Number of images to sample (split equally between train/test)")
    args = parser.parse_args()

    class_name = args.class_name
    n_total    = args.n
    n_per_split = n_total // 2

    output_dir = os.path.join(OUTPUT_ROOT, class_name)
    os.makedirs(output_dir, exist_ok=True)

    images_info = []

    for split_name, csv_path in [("train", TRAIN_SPLIT), ("test", TEST_SPLIT)]:
        if not os.path.exists(csv_path):
            print(f"[WARN] {csv_path} not found — skipping {split_name} split.")
            continue

        df = pd.read_csv(csv_path)
        subset = df[df["mapped_label"] == class_name]

        if len(subset) == 0:
            print(f"[WARN] No rows with class '{class_name}' in {split_name} split.")
            continue

        sample = subset.sample(n=min(n_per_split, len(subset)), random_state=42)
        print(f"  Sampling {len(sample)} images from {split_name} split "
              f"({len(subset)} available).")

        for _, row in sample.iterrows():
            src_path = row["image_path"]
            if not os.path.exists(src_path):
                print(f"  [MISS] {src_path} not on disk — skipping.")
                continue

            dataset   = row.get("dataset", "unknown")
            ext       = os.path.splitext(src_path)[1]
            base      = os.path.splitext(os.path.basename(src_path))[0]
            dest_name = f"{split_name}__{dataset}__{base}{ext}"
            dest_path = os.path.join(output_dir, dest_name)
            shutil.copy2(src_path, dest_path)

            images_info.append({
                "dest_filename":  dest_name,
                "source_dataset": dataset,
                "split":          split_name,
                "original_path":  src_path,
            })

    if not images_info:
        print("No images copied. Check that image files exist on disk.")
        return

    print(f"\nCopied {len(images_info)} images to {output_dir}/")
    make_html(images_info, class_name, output_dir)
    print(f"\nOpen {output_dir}/review.html in a browser to inspect.")
    print("Report back: how many images look mislabeled or unusable?")


if __name__ == "__main__":
    main()
