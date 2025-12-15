import os
import subprocess

QP_LIST = [70, 50, 30, 20, 10]
CATEGORY_LIST = [
    "laptop", "teddybear", "vase"
]

DATASET_ROOT = "/home/knuvi/datasetJPEG/jpeg"
RESULT_ROOT = "/home/knuvi/CODiff/Results/jpeg"
SCRIPT_PATH = "/home/knuvi/CODiff/main_test_codiff.py"

PRETRAINED_MODEL = "/home/knuvi/model_zoo/stable-diffusion-2-1-base"
CODIFF_PATH = "/home/knuvi/CODiff/model_zoo/codiff.pkl"
CAVE_PATH = "/home/knuvi/CODiff/model_zoo/cave.pth"

for qp in QP_LIST:
    qp_dir = f"JpegOutput_{qp}"
    qp_path = os.path.join(DATASET_ROOT, qp_dir)

    for category in CATEGORY_LIST:
        category_path = os.path.join(qp_path, category)
        if not os.path.isdir(category_path):
            continue

        for scene in sorted(os.listdir(category_path)):
            images_dir = os.path.join(category_path, scene, "images")
            if not os.path.isdir(images_dir):
                continue

            output_images_dir = os.path.join(
                RESULT_ROOT,
                qp_dir,
                category,
                scene,
                "images"
            )
            os.makedirs(output_images_dir, exist_ok=True)

            cmd = [
                "python", SCRIPT_PATH,
                "-i", images_dir,         
                "-o", output_images_dir,
                "--pretrained_model", PRETRAINED_MODEL,
                "--codiff_path", CODIFF_PATH,
                "--cave_path", CAVE_PATH
            ]

            print("▶ RUN:", " ".join(cmd))
            subprocess.run(cmd, check=True)
