#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from uuid import uuid4


def list_dataset_dirs(datasets_dir: Path):
    if not datasets_dir.exists():
        raise FileNotFoundError(f"Datasets directory not found: {datasets_dir}")
    dirs = [p for p in datasets_dir.iterdir() if p.is_dir() and not p.name.startswith('.')]
    # Sort by the number at the beginning of the directory name
    def get_sort_key(path):
        name = path.name
        # Extract number from the beginning of the name
        import re
        match = re.match(r'^(\d+)', name)
        return int(match.group(1)) if match else float('inf')
    return sorted(dirs, key=get_sort_key)


def run_cmd(cmd, cwd: Path):
    print(f"\n[RUN] ({cwd})$ {' '.join(cmd)}\n")
    subprocess.run(cmd, cwd=str(cwd), check=True)


def find_latest_dir(parent: Path) -> Path | None:
    candidates = [p for p in parent.iterdir() if p.is_dir()]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def safe_rename(src: Path, dst: Path):
    if dst.exists():
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup = dst.with_name(f"{dst.name}_old_{timestamp}")
        print(f"[INFO] Destination {dst} exists. Renaming existing to {backup}")
        dst.rename(backup)
    print(f"[INFO] Renaming {src} -> {dst}")
    src.rename(dst)


def main():
    base_dir = Path(__file__).resolve().parent
    gs_dir = base_dir / 'gaussian-splatting'
    datasets_dir = base_dir / 'datasets'
    outputs_dir = gs_dir / 'outputs'

    outputs_dir.mkdir(parents=True, exist_ok=True)

    dataset_dirs = list_dataset_dirs(datasets_dir)
    if not dataset_dirs:
        print(f"No datasets found under {datasets_dir}")
        return

    python_exec = sys.executable or 'python3'

    for ds_path in dataset_dirs:
        dataset_name = ds_path.name
        print(f"\n====================\nProcessing dataset: {dataset_name}\n====================")

        # 1) Train
        temp_run_name = uuid4().hex[:10]
        model_rel_path = f"outputs/{temp_run_name}"
        train_cmd = [
            python_exec,
            'train.py',
            '-s', str((base_dir / 'datasets' / dataset_name).resolve()),
            '--eval',
            '--disable_viewer',
            '--model_path', model_rel_path,
        ]
        try:
            run_cmd(train_cmd, cwd=gs_dir)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Training failed for {dataset_name}: {e}")
            continue

        # 2) Rename most recent outputs dir to dataset name
        latest_dir = find_latest_dir(outputs_dir)
        if latest_dir is None:
            print(f"[ERROR] No output directories found to rename for {dataset_name}")
            continue
        target_dir = outputs_dir / dataset_name
        try:
            safe_rename(latest_dir, target_dir)
        except Exception as e:
            print(f"[ERROR] Failed to rename {latest_dir} -> {target_dir}: {e}")
            continue

        # 3) Render
        render_cmd = [
            python_exec,
            'render.py',
            '-m', f"outputs/{dataset_name}",
        ]
        try:
            run_cmd(render_cmd, cwd=gs_dir)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Rendering failed for {dataset_name}: {e}")
            continue

        # 4) Metrics
        metrics_cmd = [
            python_exec,
            'metrics.py',
            '-m', f"outputs/{dataset_name}",
        ]
        try:
            run_cmd(metrics_cmd, cwd=gs_dir)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Metrics computation failed for {dataset_name}: {e}")
            continue

    print("\nAll datasets processed.")


if __name__ == '__main__':
    main()


