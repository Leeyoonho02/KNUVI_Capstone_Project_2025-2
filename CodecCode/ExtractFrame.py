import os
import subprocess
import glob

# 루트 디렉토리
root_dir = "/Volumes/T7/experiments/Blender"

# 카테고리들 (Auditorium, Museum 등)
categories = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]

# 추출할 구간
start_time = "00:00:00"
end_time = "00:01:40"

for category in categories:
    category_path = os.path.join(root_dir, category)

    # AVC_AI, AVC_RA, HEVC_AI, HEVC_RA
    for codec in os.listdir(category_path):
        codec_path = os.path.join(category_path, codec)
        if not os.path.isdir(codec_path):
            continue

        # QP22, QP32, QP42
        for qp_dir in os.listdir(codec_path):
            qp_path = os.path.join(codec_path, qp_dir)
            if not os.path.isdir(qp_path):
                continue

            # mp4 파일 찾기
            mp4_files = glob.glob(os.path.join(qp_path, "*.mp4"))
            for mp4_file in mp4_files:
                # 저장할 디렉토리 (QP22_img 등)
                save_dir = os.path.join(category_path, codec, qp_dir + "_img")
                os.makedirs(save_dir, exist_ok=True)

                # 출력 파일명 패턴
                output_pattern = os.path.join(save_dir, "frame_%03d.png")

                # ffmpeg 명령어
                '''
                cmd = [
                    "ffmpeg",
                    "-ss", start_time,
                    "-to", end_time,
                    "-i", mp4_file,
                    "-vf", "fps=1",
                    output_pattern
                ]
                '''
                cmd = [
                    "ffmpeg",
                    "-i", mp4_file,
                    "-vf", "fps=30",
                    output_pattern
                ]
                print("Running:", " ".join(cmd))
                subprocess.run(cmd)
