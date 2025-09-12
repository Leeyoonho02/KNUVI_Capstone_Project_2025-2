import os
import re
import shutil

scene = "treehill"
img_dir = fr"C:\Users\PC008\Desktop\mip-nerf360\{scene}\images"
out_dir = fr"C:\Users\PC008\Desktop\mip-nerf360\{scene}\video_frames"
os.makedirs(out_dir, exist_ok=True)

# 파일명에서 숫자 추출
def extract_number(filename):
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else -1

# 이미지 목록 불러오기
all_imgs = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

# 홀수/짝수 분류
odd_imgs = [f for f in all_imgs if extract_number(f) % 2 == 1]
even_imgs = [f for f in all_imgs if extract_number(f) % 2 == 0]


even_imgs.sort(key=extract_number)
odd_imgs.sort(key=extract_number, reverse=True)

# 최종 순서
final_sequence = even_imgs + odd_imgs

# 복사
frame_id = 0
for img_name in final_sequence:
    src = os.path.join(img_dir, img_name)
    dst = os.path.join(out_dir, f"frame_{frame_id:06d}.JPG")
    if os.path.exists(src):
        shutil.copy(src, dst)
        frame_id += 1

print(f"총 {frame_id} 장의 이미지 정렬 완료! ({out_dir})")
