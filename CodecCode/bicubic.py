import cv2
import os

# 현재 폴더의 모든 mp4 파일 가져오기
video_files = [f for f in os.listdir('.') if f.endswith('.mp4')]

for video_file in video_files:
    # 비디오 캡처
    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        print(f"Failed to open {video_file}")
        continue

    # 원본 프레임 속성
    fps = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 출력 크기: 1/4
    out_width = width // 4
    out_height = height // 4

    # 출력 파일 이름
    output_file = f"resized_{video_file}"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, fps, (out_width, out_height))

    # 앞 2분까지만 처리
    max_frames = int(fps * 120)  # 120초

    frame_count = 0
    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize (bicubic)
        resized_frame = cv2.resize(frame, (out_width, out_height), interpolation=cv2.INTER_CUBIC)

        out.write(resized_frame)
        frame_count += 1

    cap.release()
    out.release()
    print(f"{video_file} -> {output_file} 완료")
