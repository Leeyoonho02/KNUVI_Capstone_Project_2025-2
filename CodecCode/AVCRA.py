
import subprocess
import glob
import os

# 압축할 QP 값 리스트
qp_values = [22, 32, 42]

# 처리할 카테고리들
categories = ["Museum_4", "Auditorium_4"]

# 각 카테고리별로 처리
for category in categories:
    input_dir = f"c:/Users/PC016/Desktop/test/{category}/original"
    output_base_dir = f"c:/Users/PC016/Desktop/test/{category}/AVC_RA"


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
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-g", "32",  # GOP 크기
                "-bf", "3",  # B-frame 개수
                "-x264-params", f"qp={qp}:keyint=32:min-keyint=32:scenecut=0:ipratio=1:pb_ratio=1:aq-mode=0",
                output_file
            ]

            print("실행:", " ".join(cmd))
            subprocess.run(cmd, check=True)
