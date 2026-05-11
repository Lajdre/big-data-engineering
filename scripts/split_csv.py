#!/usr/bin/env python3

from pathlib import Path

import pandas as pd


def split_csv(input_path: Path, output_dir: Path, n_parts: int = 3) -> None:
  """Split CSV into n_parts and save to output_dir."""
  df = pd.read_csv(input_path)
  rows_per_part = len(df) // n_parts

  for i in range(n_parts):
    start = i * rows_per_part
    end = start + rows_per_part if i < n_parts - 1 else len(df)

    part_df = df.iloc[start:end]
    output_path = output_dir / f"part_{i + 1:02d}.csv"
    part_df.to_csv(output_path, index=False)
    print(f"Written {output_path}: {len(part_df)} rows")

  print(f"Total: {len(df)} rows split into {n_parts} files")


if __name__ == "__main__":
  split_csv(Path("data/raw_pgcb.csv"), Path("data/"), n_parts=3)
