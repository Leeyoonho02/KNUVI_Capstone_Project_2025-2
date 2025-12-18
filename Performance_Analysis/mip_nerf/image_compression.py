#!/usr/bin/env python3

import os
import re
from PIL import Image

# =========================
# 사용자 설정
# =========================
base_root = os.path.expanduser("~/Mip-NeRF360")
output_root = os.path.expanduser("~/Mip-NeRF360_JPEG")

jpeg_quality_list = [10, 30, 50, 70, 90]
num_digits = 5  # 00000.jpg

# =========================
# 유틸: 파일명 숫자 기준 정렬
# (_DSC8679.jpg → 8679)
# =========================
def extract_number(filename):
    m = re.search(r'(\d+)', filename)
    return int(m.group(1)) if m else -1

# =========================
# 카테고리(씬) 탐색
# =========================
categories = [
    d for d in os.listdir(base_root)
    if os.path.isdir(os.path.join(base_root, d))
]

for category in categories:
    category_path = os.path.join(base_root, category)
    images_path = os.path.join(category_path, "images")

    if not os.path.isdir(images_path):
        print(f"⚠️ {images_path} 가 존재하지 않습니다. 건너뜁니다.")
        continue

    # 이미지 파일 수집 + 정렬
    files = [
        f for f in os.listdir(images_path)
        if (
            not f.startswith(".") and          # 숨김 파일 제외
            not f.startswith("._") and          # AppleDouble 제외
            f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff"))
        )
    ]


    if not files:
        print(f"⚠️ {images_path} 에 이미지 파일이 없습니다.")
        continue

    files = sorted(files, key=extract_number)

    for jpeg_quality in jpeg_quality_list:
        # 품질별 출력 폴더
        output_dir = os.path.join(
            output_root,
            f"JpegOutput_{jpeg_quality}",
            category,
            "images"
        )
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n🚀 처리 시작: Scene={category}, JPEG Q={jpeg_quality}")

        for idx, file in enumerate(files):
            img_path = os.path.join(images_path, file)

            try:
                with Image.open(img_path) as img:
                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    save_name = f"{idx:0{num_digits}d}.jpg"
                    save_path = os.path.join(output_dir, save_name)

                    img.save(
                        save_path,
                        "JPEG",
                        quality=jpeg_quality,
                        optimize=True
                    )

            except Exception as e:
                print(f"❌ {img_path} 처리 중 오류: {e}")

        print(f"✅ 완료: Scene={category}, Q={jpeg_quality} → {output_dir}")

print("\n🎉 모든 카테고리 / JPEG 품질 처리 완료!")
