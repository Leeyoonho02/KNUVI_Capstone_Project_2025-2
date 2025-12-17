import os
import re
import subprocess
import pathlib

# =========================
# 경로 설정
# =========================
base_dir = "/dataset"
output_base = "/datasetAVC/avc"

category_list = [
    "backpack", "ball", "book", "bottle", "chair",
    "cup", "handbag", "laptop", "plant", "teddybear", "vase"
]

qp_list = [27, 32, 37, 42, 47]

pattern = re.compile(r"^\d+_\d+_\d+$")

# =========================
# 유틸 함수
# =========================
def extract_last_number(filename):
    nums = re.findall(r"\d+", filename)
    return int(nums[-1]) if nums else 0


# =========================
# 메인 루프
# =========================
for qp in qp_list:
    for category in category_list:
        category_path = os.path.join(base_dir, category)
        if not os.path.isdir(category_path):
            continue

        for subfolder in sorted(os.listdir(category_path)):
            if not pattern.match(subfolder):
                continue

            image_dir = os.path.join(category_path, subfolder, "images")
            if not os.path.isdir(image_dir):
                continue

            # ✅ 메타데이터 제외 + 숫자 기준 정렬
            files = sorted(
                [
                    f for f in os.listdir(image_dir)
                    if f.lower().endswith(".jpg") and not f.startswith(".")
                ],
                key=extract_last_number
            )

            if not files:
                continue

            # =========================
            # 출력 디렉토리
            # =========================
            output_dir = os.path.join(
                output_base,
                f"AvcOutput_{qp}",
                category,
                subfolder,
                "images"
            )
            os.makedirs(output_dir, exist_ok=True)

            temp_video = os.path.join(output_dir, f"temp_qp{qp}.mp4")
            list_file = os.path.join(output_dir, "input_list.txt")

            # =========================
            # ffmpeg 입력 리스트 생성
            # =========================
            with open(list_file, "w") as f:
                for fname in files:
                    f.write(f"file '{os.path.join(image_dir, fname)}'\n")

            # =========================
            # 1️⃣ JPG → AVC 영상
            # =========================
            cmd_compress = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-r", "30",
                "-i", list_file,
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-c:v", "libx264",
                "-profile:v", "high",
                "-preset", "slow",
                "-qp", str(qp),
                "-pix_fmt", "yuv420p",
                "-r", "30",
                temp_video
            ]
            subprocess.run(cmd_compress, check=True)

            # =========================
            # 2️⃣ 영상 → PNG 프레임 추출
            # =========================
            cmd_extract = [
                "ffmpeg", "-y",
                "-i", temp_video,
                "-r", "30",
                os.path.join(output_dir, "tmp_%06d.png")
            ]
            subprocess.run(cmd_extract, check=True)

            # =========================
            # 3️⃣ rename (실제 생성된 tmp 기준)
            # =========================
            tmp_files = sorted(
                f for f in os.listdir(output_dir)
                if f.startswith("tmp_") and f.lower().endswith(".png")
            )

            if len(tmp_files) != len(files):
                print(
                    f"⚠️ 프레임 수 불일치 | "
                    f"{category}/{subfolder} | "
                    f"JPG={len(files)} PNG={len(tmp_files)}"
                )

            for orig_file, tmp_name in zip(files, tmp_files):
                orig_stem = pathlib.Path(orig_file).stem
                src = os.path.join(output_dir, tmp_name)
                dst = os.path.join(output_dir, f"{orig_stem}_AVC_{qp}.png")
                os.rename(src, dst)

            # =========================
            # 정리
            # =========================
            os.remove(temp_video)
            os.remove(list_file)

            print(f"✅ 완료: AvcOutput_{qp}/{category}/{subfolder}")
