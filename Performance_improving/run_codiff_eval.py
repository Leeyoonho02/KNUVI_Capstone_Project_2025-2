import os
import sys
import argparse
import cv2
import numpy as np
import torch
from torchvision import transforms
from PIL import Image
from tqdm import tqdm
from skimage.metrics import peak_signal_noise_ratio as compare_psnr
from skimage.metrics import structural_similarity as compare_ssim

# -------------------------------------------------------------------------
# 1. 경로 및 라이브러리 설정
# -------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
codiff_root = os.path.join(current_dir, 'CODiff')

sys.path.insert(0, codiff_root)
sys.path.insert(0, os.path.join(codiff_root, 'diffusion'))
sys.path.insert(0, os.path.join(codiff_root, 'diffusion', 'my_utils'))

try:
    from diffusion.codiff import CODiff_test
    from diffusion.my_utils.wavelet_color_fix import adain_color_fix, wavelet_color_fix
    import utils.utils_image as utils
    from cave.cave import CaVE
    import pyiqa
except ImportError as e:
    print(f"[Error] Import 실패: {e}")
    sys.exit(1)

import warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------------------------------
# 2. 설정값 정의
# -------------------------------------------------------------------------
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--codiff_path', type=str, default=os.path.join(codiff_root, 'model_zoo', 'codiff.pkl'))
    parser.add_argument('--cave_path', type=str, default=os.path.join(codiff_root, 'model_zoo', 'cave.pth'))
    parser.add_argument('--pretrained_model', type=str, default=os.path.join(codiff_root, 'model_zoo', 'stable-diffusion-2-1-base'))
    parser.add_argument('--output_dir', type=str, default='./results')
    parser.add_argument('--mixed_precision', type=str, default='fp16')
    parser.add_argument('--process_size', type=int, default=512)
    parser.add_argument('--vae_encoder_tiled_size', type=int, default=1024)
    parser.add_argument('--vae_decoder_tiled_size', type=int, default=224)
    parser.add_argument('--latent_tiled_size', type=int, default=96)
    parser.add_argument('--latent_tiled_overlap', type=int, default=32)
    parser.add_argument('--align_method', type=str, default='adain', choices=['adain', 'wavelet', 'nofix'])
    parser.add_argument('--merge_and_unload_lora', action='store_true', default=False)
    parser.add_argument('--offload_lora', action='store_true', default=False)
    parser.add_argument('--lora_scale', type=float, default=1.0)
    parser.add_argument('--tile_diffusion', action='store_true', default=False)
    
    return parser.parse_args()

def main():
    args = get_args()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # 모델 로딩
    model = CODiff_test(args)
    cave = CaVE(in_nc=3, out_nc=3, nc=[64,128,256,512], nb=4, act_mode='BR')
    cave.load_state_dict(torch.load(args.cave_path, map_location=device), strict=True)
    cave.eval().to(device)
    for p in cave.parameters(): p.requires_grad = False

    # IQA Metrics 설정
    metric_names = ['lpips', 'dists', 'niqe', 'musiq', 'maniqa', 'clipiqa']
    iqa_metrics = {m: pyiqa.create_metric(m, device=device) for m in metric_names}

    # 매핑 설정
    quality_configs = [
        ('jpeg10', 'gt_for_jpeg10', 10),
        ('jpeg50', 'gt', 50),
        ('jpeg70', 'gt', 70)
    ]

    os.makedirs(args.output_dir, exist_ok=True)
    csv_path = os.path.join(args.output_dir, 'results.csv')
    
    # -------------------------------------------------------------------------
    # CSV 헤더 생성 (순서 고정: PSNR -> SSIM -> PyIQA 순서로 Before/After 쌍)
    # -------------------------------------------------------------------------
    header = ['quality', 'img_name', 'psnr_before', 'psnr_after', 'ssim_before', 'ssim_after']
    for m in metric_names:
        header += [f'{m}_before', f'{m}_after']
    
    with open(csv_path, 'w') as f:
        f.write(','.join(header) + '\n')

    # 루프 시작
    for input_folder, gt_folder, qf in quality_configs:
        if not os.path.exists(input_folder): continue

        print(f"\n>> Processing: {input_folder}")
        save_dir = os.path.join(args.output_dir, input_folder, 'denoised')
        os.makedirs(save_dir, exist_ok=True)

        img_list = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

        for img_name in tqdm(img_list, desc=f"QF {qf}"):
            try:
                # 이미지 로드
                img_L_pil = Image.open(os.path.join(input_folder, img_name)).convert('RGB')
                
                base_name = os.path.splitext(img_name)[0]
                gt_path = os.path.join(gt_folder, img_name)
                if not os.path.exists(gt_path):
                    for ext in ['.png', '.jpg', '.jpeg']:
                        if os.path.exists(os.path.join(gt_folder, base_name + ext)):
                            gt_path = os.path.join(gt_folder, base_name + ext); break
                if not os.path.exists(gt_path): continue
                img_GT_pil = Image.open(gt_path).convert('RGB')
                
                # 사이즈 조정 (8배수)
                w, h = img_L_pil.size
                new_w, new_h = w - w % 8, h - h % 8
                img_L_pil = img_L_pil.resize((new_w, new_h), Image.LANCZOS)
                img_GT_pil = img_GT_pil.resize((new_w, new_h), Image.LANCZOS)

                # Numpy 변환 (PSNR/SSIM용)
                lq_np = np.array(img_L_pil)
                gt_np = np.array(img_GT_pil)

                # 텐서 변환 (Metrics용)
                lq_tensor = transforms.ToTensor()(img_L_pil).unsqueeze(0).to(device)
                gt_tensor = transforms.ToTensor()(img_GT_pil).unsqueeze(0).to(device)

                # Inference
                lq_norm = lq_tensor * 2 - 1
                with torch.no_grad():
                    visual_emb = cave.get_visual_embedding(lq_tensor)
                    output = model(lq_norm, visual_emb)
                
                img_E_pil = transforms.ToPILImage()(output[0].cpu() * 0.5 + 0.5)
                if args.align_method == 'adain': img_E_pil = adain_color_fix(target=img_E_pil, source=img_L_pil)
                elif args.align_method == 'wavelet': img_E_pil = wavelet_color_fix(target=img_E_pil, source=img_L_pil)
                
                # 저장 및 After Numpy 변환
                img_E_pil.save(os.path.join(save_dir, img_name))
                out_np = np.array(img_E_pil)
                out_tensor = transforms.ToTensor()(img_E_pil).unsqueeze(0).to(device)

                # ---------------------------------------------------------------------
                # 수치 계산 (Row 구성)
                # ---------------------------------------------------------------------
                psnr_before = compare_psnr(gt_np, lq_np)
                psnr_after = compare_psnr(gt_np, out_np)
                
                # SSIM (Channel axis 대응)
                try:
                    ssim_before = compare_ssim(gt_np, lq_np, channel_axis=2)
                    ssim_after = compare_ssim(gt_np, out_np, channel_axis=2)
                except:
                    ssim_before = compare_ssim(gt_np, lq_np, multichannel=True)
                    ssim_after = compare_ssim(gt_np, out_np, multichannel=True)

                # 기본 정보 추가
                row = [qf, base_name, psnr_before, psnr_after, ssim_before, ssim_after]
                
                # PyIQA 모든 지표 Before/After 추가
                for m_name in metric_names:
                    m_func = iqa_metrics[m_name]
                    with torch.no_grad():
                        score_before = m_func(lq_tensor, gt_tensor).item()
                        score_after = m_func(out_tensor, gt_tensor).item()
                    row += [score_before, score_after]

                # CSV 쓰기
                with open(csv_path, 'a') as f:
                    f.write(','.join(map(str, row)) + '\n')

            except Exception as e:
                print(f"\n[Error] {img_name} 실패: {e}")

    print(f"\n>> 완료! 모든 지표의 Before/After가 {csv_path}에 저장되었습니다.")

if __name__ == '__main__':
    main()
