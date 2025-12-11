import os
import shutil
import glob

# QP 값과 Category 값 설정
QP_values = [70, 50, 30, 20, 10]
categories = ["backpack", "ball", "book", "bottle", "chair", "cup", "handbag", "laptop", "plant", "teddybear", "vase"]

# 이미지 파일이 있는 디렉토리 및 복사 대상 디렉토리 설정
source_dir_template = "/home/knuvi/datasetJPEG/jpeg/JpegOutput_{QP}/{category}/*/images"
destination_dir = "/home/knuvi/vggt/temp/images"  # 이미지 복사 위치
temp_dir = "/home/knuvi/vggt/temp"  # demo_colmap.py가 읽는 폴더 경로
result_dir_template = "/home/knuvi/vggt/Result/jpeg/JpegOutput_{QP}/{category}/{filename}/sparse"

# destination_dir이 없으면 생성
if not os.path.exists(destination_dir):
    os.makedirs(destination_dir)
else:
    # temp/images 디렉토리가 비어 있지 않으면 비워준다
    for filename in os.listdir(destination_dir):
        file_path = os.path.join(destination_dir, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

# 이미지 복사 및 demo_colmap 실행
for QP in QP_values:
    for category in categories:
        # 해당 카테고리 및 QP에 맞는 이미지 디렉토리 경로 패턴 설정
        source_dir_pattern = source_dir_template.format(QP=QP, category=category)

        # glob을 사용하여 해당 패턴에 맞는 폴더를 찾음
        folder_paths = glob.glob(source_dir_pattern)

        if not folder_paths:
            print(f"디렉토리 없음: {source_dir_pattern}")
            continue

        # 각 폴더에 대해 작업 수행
        for folder_path in folder_paths:
            print(f"폴더 경로: {folder_path}")
            # .jpg로 수정 및 이미지 파일 리스트 정렬
            image_files = sorted([f for f in os.listdir(folder_path) if f.endswith(f"JPEG_{QP}.jpg")])

            # 이미지 파일을 하나씩 복사하여 처리
            for image_file in image_files:
                source_file = os.path.join(folder_path, image_file)

                if os.path.exists(source_file):
                    # 파일 이름을 폴더 이름으로 사용
                    filename = os.path.splitext(image_file)[0]  # 확장자 제거
                    result_folder = result_dir_template.format(QP=QP, category=category, filename=filename)

                    # 결과 저장 폴더가 없으면 생성
                    if not os.path.exists(result_folder):
                        os.makedirs(result_folder)

                    # temp/images 디렉토리에 한 장씩 복사
                    shutil.copy(source_file, destination_dir)

                    # 출력: 복사된 파일과 저장되는 폴더 경로
                    print(f"복사된 파일: {source_file} -> {destination_dir}")
                    print(f"저장되는 결과 폴더: {result_folder}")

                    # demo_colmap 실행 (--scene_dir에는 temp 경로만 전달)
                    os.system(f"python demo_colmap.py --scene_dir {temp_dir}")

                    # 처리된 후 temp/images 디렉토리 비우기
                    os.remove(os.path.join(destination_dir, image_file))

                    # sparse 폴더 내 파일을 result_folder로 복사
                    sparse_folder = os.path.join(temp_dir, "sparse")
                    if os.path.exists(sparse_folder):
                        for file_name in os.listdir(sparse_folder):
                            file_path = os.path.join(sparse_folder, file_name)
                            if os.path.isfile(file_path):
                                shutil.copy(file_path, result_folder)
                                # 출력: 복사된 결과 파일
                                print(f"복사된 결과 파일: {file_path} -> {result_folder}")
                    else:
                        print(f"sparse 폴더가 존재하지 않음: {sparse_folder}")

                else:
                    print(f"파일이 존재하지 않음: {source_file}")
