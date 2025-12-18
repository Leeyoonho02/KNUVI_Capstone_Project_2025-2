import os
import shutil
import glob
import random

# =============================
# 설정
# =============================
QP_values = [70, 50, 30, 20, 10]
categories = [
    "backpack", "ball", "book", "bottle", "chair",
    "cup", "handbag", "laptop", "plant", "teddybear", "vase"
]

osediff_root = "/home/knuvi/OSEDiff/Results/jpeg"
dataset_root = "/home/knuvi/dataset"
datasetjpeg_root = "/home/knuvi/datasetJPEG/jpeg"

temp1 = "/home/knuvi/vggt/temp1"  # OSEDiff
temp2 = "/home/knuvi/vggt/temp2"  # dataset
temp3 = "/home/knuvi/vggt/temp3"  # datasetJPEG

result_after = "/home/knuvi/vggt/Result/After10"
result_before = "/home/knuvi/vggt/Result/Before10"
result_before_jpeg = "/home/knuvi/vggt/Result/Before10_JPEG"

# =============================
# 유틸 함수
# =============================
def reset_temp(base):
    if os.path.exists(base):
        shutil.rmtree(base)
    os.makedirs(os.path.join(base, "images"))

def write_inputlist(scene_dir, filenames):
    with open(os.path.join(scene_dir, "inputlist.txt"), "w") as f:
        for name in filenames:
            f.write(name + "\n")

def move_sparse(scene_dir, dst_root):
    sparse_src = os.path.join(scene_dir, "sparse")
    os.makedirs(dst_root, exist_ok=True)
    shutil.move(sparse_src, os.path.join(dst_root, "sparse"))

# =============================
# 메인 루프
# =============================
for QP in QP_values:
    for category in categories:
        scenes = glob.glob(
            f"{osediff_root}/JpegOutput_{QP}/{category}/*"
        )

        for scene_path in scenes:
            scene = os.path.basename(scene_path)

            osediff_images_dir = f"{scene_path}/images"
            dataset_images_dir = f"{dataset_root}/{category}/{scene}/images"
            datasetjpeg_images_dir = (
                f"{datasetjpeg_root}/JpegOutput_{QP}/{category}/{scene}/images"
            )

            # -----------------------------
            # OSEDiff 기준 frame 선택
            # -----------------------------
            osediff_images = [
                f for f in os.listdir(osediff_images_dir)
                if f.endswith(f"_JPEG_{QP}.jpg")
            ]

            if len(osediff_images) < 10:
                print(f"[SKIP] {scene} (images < 10)")
                continue

            selected_images = random.sample(osediff_images, 10)
            selected_frames = [f[:11] for f in selected_images]

            # 로그
            print("\n[FRAME SELECTION]")
            print(f"QP={QP} | category={category} | scene={scene}")
            print(f"- selected frames: {selected_frames}")

            # =============================
            # 1️⃣ OSEDiff → After10
            # =============================
            reset_temp(temp1)
            osediff_files = []

            for fname in selected_images:
                shutil.copy(
                    os.path.join(osediff_images_dir, fname),
                    os.path.join(temp1, "images", fname)
                )
                osediff_files.append(fname)

            write_inputlist(temp1, osediff_files)
            os.system(f"python demo_colmap.py --scene_dir {temp1}")

            move_sparse(
                temp1,
                f"{result_after}/QP{QP}/{category}/{scene}"
            )

            # =============================
            # 2️⃣ dataset → Before10
            # =============================
            reset_temp(temp2)
            dataset_files = []

            for fid in selected_frames:
                fname = f"{fid}.jpg"
                shutil.copy(
                    os.path.join(dataset_images_dir, fname),
                    os.path.join(temp2, "images", fname)
                )
                dataset_files.append(fname)

            write_inputlist(temp2, dataset_files)
            os.system(f"python demo_colmap.py --scene_dir {temp2}")

            move_sparse(
                temp2,
                f"{result_before}/QP{QP}/{category}/{scene}"
            )

            # =============================
            # 3️⃣ datasetJPEG → Before10_JPEG
            # =============================
            reset_temp(temp3)
            jpeg_files = []

            for fid in selected_frames:
                fname = f"{fid}_JPEG_{QP}.jpg"
                shutil.copy(
                    os.path.join(datasetjpeg_images_dir, fname),
                    os.path.join(temp3, "images", fname)
                )
                jpeg_files.append(fname)

            write_inputlist(temp3, jpeg_files)
            os.system(f"python demo_colmap.py --scene_dir {temp3}")

            move_sparse(
                temp3,
                f"{result_before_jpeg}/QP{QP}/{category}/{scene}"
            )

            print(f"[DONE] QP{QP} | {category} | {scene}")
