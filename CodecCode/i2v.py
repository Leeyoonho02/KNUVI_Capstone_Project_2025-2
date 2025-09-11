#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List

# ------------- 사용자 설정 -------------
input_dir = "/Volumes/T7/experiments/Blender/lego/Original"      # 원본 이미지 폴더 (파일명 제각각 가능)
work_dir = "/Volumes/T7/experiments/Mip-NeRF360/temp"        # 임시 프레임 폴더 (자동 생성)
output_dir = "/Volumes/T7/experiments/Blender/lego/test"          # 최종 인코딩 결과 저장 폴더
fps = 30                        # 원하는 fps (예: 30)
qp_values = [22, 32, 42]        # 고정 QP 리스트
order_by = "natural"            # "natural" 또는 "mtime" (파일 생성/수정시간)
# ---------------------------------------

os.makedirs(work_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# Natural sort helper
def natural_key(s: str):
    parts = re.split(r'(\d+)', s)
    return [int(p) if p.isdigit() else p.lower() for p in parts]

# Gather image files
p = Path(input_dir)
if not p.exists():
    raise SystemExit(f"input_dir '{input_dir}' not found")

# 허용 확장자 + 숨김(. 으로 시작) 파일 스킵
exts = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp'}
files = [
    f for f in p.iterdir()
    if f.is_file()
    and not f.name.startswith('.')       # 메타 data 스킵
    and f.suffix.lower() in exts
]

if not files:
    raise SystemExit("No image files found in input_dir")

# Sort files
if order_by == "natural":
    files.sort(key=lambda x: natural_key(x.name))
elif order_by == "mtime":
    files.sort(key=lambda x: x.stat().st_mtime)
else:
    files.sort()  # fallback

# Create sequential symlinks (or copies if symlink not allowed)
def prepare_sequential(files: List[Path], dest_dir: Path):
    # clear dest_dir
    for z in dest_dir.iterdir():
        if z.is_file() or z.is_symlink():
            z.unlink()
    # make sequential links
    for i, src in enumerate(files, start=1):
        ext = src.suffix.lower()
        dest_name = f"frame_{i:04d}{ext}"
        dest_path = dest_dir / dest_name
        try:
            # prefer symlink
            os.symlink(src.resolve(), dest_path)
        except Exception:
            shutil.copy2(src, dest_path)

prepare_sequential(files, Path(work_dir))

# Determine image pattern for ffmpeg (use first file's extension)
first_ext = Path(files[0]).suffix.lower()
image_pattern = os.path.join(work_dir, f"frame_%04d{first_ext}")

# Encoding function
def encode_sequence(codec: str, mode: str, qp: int):
    if codec == "avc":
        encoder = "libx264"
        param_flag = "-x264-params"
    elif codec == "hevc":
        encoder = "libx265"
        param_flag = "-x265-params"
    else:
        raise ValueError("codec must be 'avc' or 'hevc'")

    if mode == "AI":
        # All-Intra: keyint=1 (모든 프레임 I-frame)
        xparams = f"qp={qp}:keyint=1:min-keyint=1:no-scenecut=1"
        out_name = f"{codec}_AI_QP{qp}.mp4"
        
    elif mode == "RA":
        # Random Access: GOP=32
        xparams = f"qp={qp}:keyint=32:min-keyint=32:scenecut=0ipratio=1:pb_ratio=1:aq-mode=0"
        out_name = f"{codec}_RA_QP{qp}.mp4"
    else:
        raise ValueError("mode must be 'AI' or 'RA'")

    output_path = os.path.join(output_dir, out_name)
    if mode == "AI":
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(fps),
            "-i", image_pattern,
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # 홀수 해상도 대응
            "-c:v", encoder,
            "-preset", "veryfast",
            param_flag, xparams,
            "-pix_fmt", "yuv420p",
            os.path.join(output_dir, out_name)
        ]
    elif mode == "RA":
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(fps),
            "-i", image_pattern,
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v", encoder,
            "-preset", "veryfast",
            "-g", "32",
            "-bf", "3",
            param_flag, xparams,
            "-pix_fmt", "yuv420p",
            os.path.join(output_dir, out_name)
        ]


    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

# Run encodes for all combos
try:
    for qp in qp_values:
        encode_sequence("avc", "AI", qp)
        encode_sequence("avc", "RA", qp)
        encode_sequence("hevc", "AI", qp)
        encode_sequence("hevc", "RA", qp)
    print("✅ 모든 인코딩 완료. 결과는:", output_dir)
finally:
    # 필요하면 temp_frames 지우기 (주석 처리하면 보존됨)
    try:
        shutil.rmtree(work_dir)
    except Exception as e:
        print("Could not remove temp directory:", e)
