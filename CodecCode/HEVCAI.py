import subprocess
import glob
import os

# 압축할 QP 값 리스트
qp_values = [22, 32, 42]

# 처리할 카테고리들
categories = ["Museum_4", "Auditorium_4"]

for category in categories:
    input_dir = f"c:/Users/PC016/Desktop/test/{category}/original"
    output_base_dir = f"c:/Users/PC016/Desktop/test/{category}/HEVC_AI_4"

    mp4_files = glob.glob(os.path.join(input_dir, "*.mp4"))

    for f in mp4_files:
        for qp in qp_values:
            # QP별 디렉토리 생성
            output_dir = os.path.join(output_base_dir, f"QP{qp}")
            os.makedirs(output_dir, exist_ok=True)

            # 출력 파일 이름: {Category}_QP{value}.mp4
            output_file = os.path.join(output_dir, f"{category}_QP{qp}.mp4")

            cmd = [
                "ffmpeg",
                "-i", f,
                "-c:v", "libx265",
                "-preset", "veryfast",
                "-g", "1",        # All-Intra: GOP=1
                "-x265-params", f"qp={qp}:keyint=1:min-keyint=1:no-scenecut=1:ipratio=1:pb_ratio=1:aq-mode=0",
                output_file
            ]

            print("실행:", " ".join(cmd))
            subprocess.run(cmd, check=True)

