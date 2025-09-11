import subprocess
import glob
import os

# 압축할 QP 값 리스트
qp_values = [22, 32, 42]

# 처리할 카테고리
categories = ["Museum", "Auditorium"]

# 처리 구간: 시작 시각과 길이
start_time = "00:00:00"
duration = "00:02:00"

# bicubic 4배 축소: 가로/세로 각각 1/2
scale_filter = "scale=iw/2:ih/2:flags=bicubic"

# 코덱/모드 설정
modes = {
    "HEVC_RA_4": {"codec": "libx265", "gop": 32},   # Random Access GOP 32
    "AVC_AI_4":  {"codec": "libx264", "gop": 1},    # All-Intra GOP 1
    "AVC_RA_4":  {"codec": "libx264", "gop": 32}    # Random Access GOP 32
}

def make_ffmpeg_cmd(input_file, output_file, codec, gop, qp):
    """FFmpeg 명령어 배열 생성"""
    if codec == "libx265":
        x265_params = f"qp={qp}:keyint={gop}:min-keyint={gop}:scenecut=0:ipratio=1:pb_ratio=1:aq-mode=0"
        return [
            "ffmpeg",
            "-ss", start_time,
            "-t", duration,
            "-i", input_file,
            "-vf", scale_filter,
            "-c:v", codec,
            "-preset", "veryfast",
            "-g", str(gop),
            "-x265-params", x265_params,
            output_file
        ]
    else:  # libx264
        x264_params = f"qp={qp}:ipratio=1:pb_ratio=1:keyint={gop}:min-keyint={gop}:no-scenecut=1"
        return [
            "ffmpeg",
            "-ss", start_time,
            "-t", duration,
            "-i", input_file,
            "-vf", scale_filter,
            "-c:v", codec,
            "-preset", "veryfast",
            "-g", str(gop),
            "-x264-params", x264_params,
            output_file
        ]

for category in categories:
    input_dir = f"c:/Users/PC016/Desktop/test/{category}/original"
    mp4_files = glob.glob(os.path.join(input_dir, "*.mp4"))

    for f in mp4_files:
        for mode_name, mode_info in modes.items():
            output_base_dir = f"c:/Users/PC016/Desktop/test/{category}/{mode_name}"

            for qp in qp_values:
                # QP별 디렉토리 생성
                output_dir = os.path.join(output_base_dir, f"QP{qp}")
                os.makedirs(output_dir, exist_ok=True)

                # 출력 파일 이름
                output_file = os.path.join(output_dir, f"{category}_QP{qp}.mp4")

                # FFmpeg cmd 배열 생성
                cmd = make_ffmpeg_cmd(f, output_file, mode_info["codec"], mode_info["gop"], qp)

                print("실행:", " ".join(cmd))
                subprocess.run(cmd, check=True)
