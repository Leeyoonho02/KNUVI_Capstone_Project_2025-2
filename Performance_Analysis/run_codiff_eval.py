import os
import sys
import argparse
import cv2
import numpy as np
import torch
from torchvision import transforms
from PIL import Image
from tqdm import tqdm

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
    from skimage.metrics import peak_signal_noise_ratio as compare_psnr
    from skimage.metrics import structural_similarity as compare_ssim
except ImportError as e:
    print(f"[Error] Import 실패: {e}")
    sys.exit(1)

# -------------------------------------------------------------------------
# 2. 설정값 정의
# -------------------------------------------------------------------------
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--codiff_path', type=str, default=os.path.join(codiff_root, 'model_zoo', 'codiff.pkl'))
    parser.add_argument('--cave_path', type=str, default=os.path.join(codiff_root, 'model_zoo', 'cave.pth'))
    parser.add_argument('--pretrained_model', type=str, default=os.path.join(codiff_root, 'model_zoo', 'stable-diffusion-2-1-base'))
    parser.add_argument('--image_path', type=str, default='./test_data')
    parser.add_argument('--output_dir', type=str, default='./results')
    parser.add_argument('--mixed_precision', type=str, default='fp16')
    parser.add_argument('--process_size', type=int, default=512)
    parser.add_argument('--vae_encoder_tiled_size', type=int, default=224)
    parser.add_argument('--vae_encoder_tiled_overlap', type=int, default=0)
    parser.add_argument('--vae_decoder_tiled_size', type=int, default=224)
    parser.add_argument('--vae_decoder_tiled_overlap', type=int, default=0)
    parser.add_argument('--latent_tiled_size', type=int, default=96)
    parser.add_argument('--latent_tiled_overlap', type=int, default=32)
    parser.add_argument('--merge_and_unload_lora', action='store_true')
    parser.add_argument('--offload_lora', action='store_true')
    parser.add_argument('--lora_scale', type=float, default=1.0)
    parser.add_argument('--tile_diffusion', action='store_true')
    parser.add_argument('--tile_diffusion_size', type=int, default=1024)
    parser.add_argument('--tile_diffusion_stride', type=int, default=512)
    parser.add_argument('--align_method', type=str, default='adain', choices=['adain', 'wavelet', 'nofix'])
    
    args = parser.parse_args()  # parse_known_args() → parse_args()로 변경
    return args

# -------------------------------------------------------------------------
# 3. 메인 실행 로직
# -------------------------------------------------------------------------
def main():
    args = get_args()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    print(f">> CODiff 모델 로딩 중... ({args.codiff_path})")
    try:
        model = CODiff_test(args)
    except Exception as e:
        print(f"모델 로드 실패: {e}")
        return

    print(f">> CaVE 모델 로딩 중... ({args.cave_path})")
    cave = CaVE(in_nc=3, out_nc=3, nc=[64,128,256,512], nb=4, act_mode='BR')
    if os.path.exists(args.cave_path):
        cave.load_state_dict(torch.load(args.cave_path, map_location=device), strict=True)
    else:
        print(f"CaVE 체크포인트 없음: {args.cave_path}")
        sys.exit(1)
        
    cave.eval().to(device)
    for p in cave.parameters(): p.requires_grad = False

    # IQA Metrics 준비 (LPIPS 포함)
    print(">> IQA Metrics 로딩 중...")
    iqa_metrics = {}
    try:
        iqa_metrics['lpips'] = pyiqa.create_metric('lpips', device=device)
    except Exception as e:
        print(f"LPIPS 로딩 실패: {e}")

    # 데이터셋 설정
    quality_folders = [('jpeg10', 'gt_for_jpeg10'), ('jpeg50', 'gt'), ('jpeg70', 'gt')]
    os.makedirs(args.output_dir, exist_ok=True)
    csv_path = os.path.join(args.output_dir, 'results.csv')

    if not os.path.exists(csv_path):
        with open(csv_path, 'w') as f:
            header = ['quality','img_name','psnr_before','psnr_after','ssim_before','ssim_after','lpips']
            f.write(','.join(header)+'\n')

    for qf_str, gt_folder in quality_folders:
        input_folder = qf_str
        if not os.path.exists(input_folder):
            print(f"폴더 없음, 건너뜀: {input_folder}")
            continue

        img_list = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg','.png','.jpeg'))])

        for img_name in tqdm(img_list, desc=f"Processing {qf_str}"):
            try:
                img_path = os.path.join(input_folder, img_name)
                img_H = Image.open(img_path).convert('RGB')
                w, h = img_H.size
                new_w, new_h = w - w % 8, h - h % 8
                img_H = img_H.resize((new_w,new_h), Image.LANCZOS)
                img_H_np = np.array(img_H)

                # JPEG 압축 시뮬레이션
                if img_H_np.shape[-1]==3:
                    img_temp = cv2.cvtColor(img_H_np, cv2.COLOR_RGB2BGR)
                else:
                    img_temp = img_H_np
                
                quality = int(qf_str.replace('jpeg',''))
                _, enc = cv2.imencode('.jpg', img_temp, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                img_L_cv = cv2.imdecode(enc, 3)
                img_L_pil = Image.fromarray(cv2.cvtColor(img_L_cv, cv2.COLOR_BGR2RGB))
                img_L_np = np.array(img_L_pil)

                lq_tensor = transforms.ToTensor()(img_L_pil).unsqueeze(0).to(device)
                lq_norm = lq_tensor * 2 - 1

                # --- Inference ---
                with torch.no_grad():
                    visual_emb = cave.get_visual_embedding(lq_tensor)
                    output = model(lq_norm, visual_emb)
                    if isinstance(output,(list,tuple)):
                        output = output[0]

                out_img = transforms.ToPILImage()(output.cpu().squeeze(0)*0.5+0.5)

                # Color Correction
                if args.align_method=='adain':
                    out_img = adain_color_fix(target=out_img, source=img_L_pil)
                elif args.align_method=='wavelet':
                    out_img = wavelet_color_fix(target=out_img, source=img_L_pil)

                out_np = np.array(out_img)

                save_dir = os.path.join(args.output_dir, qf_str, 'denoised')
                os.makedirs(save_dir, exist_ok=True)
                out_img.save(os.path.join(save_dir, img_name))

                # Metrics 계산
                base_name = os.path.splitext(img_name)[0]
                gt_path = os.path.join(gt_folder, img_name)
                if not os.path.exists(gt_path):
                    for ext in ['.png','.jpg','.jpeg']:
                        if os.path.exists(os.path.join(gt_folder, base_name+ext)):
                            gt_path = os.path.join(gt_folder, base_name+ext)
                            break

                if os.path.exists(gt_path):
                    img_GT = Image.open(gt_path).convert('RGB').resize((new_w,new_h), Image.LANCZOS)
                    gt_np = np.array(img_GT)
                    gt_tensor = transforms.ToTensor()(img_GT).unsqueeze(0).to(device)
                    out_tensor = transforms.ToTensor()(out_img).unsqueeze(0).to(device)

                    psnr_before = compare_psnr(gt_np, img_L_np)
                    psnr_after  = compare_psnr(gt_np, out_np)
                    
                    try:
                        ssim_before = compare_ssim(gt_np, img_L_np, channel_axis=2)
                        ssim_after  = compare_ssim(gt_np, out_np, channel_axis=2)
                    except TypeError:
                        ssim_before = compare_ssim(gt_np, img_L_np, multichannel=True)
                        ssim_after  = compare_ssim(gt_np, out_np, multichannel=True)

                    with torch.no_grad():
                        lpips_val = iqa_metrics['lpips'](out_tensor, gt_tensor).item() if 'lpips' in iqa_metrics else -1

                    with open(csv_path,'a') as f:
                        row = [quality, base_name, psnr_before, psnr_after, ssim_before, ssim_after, lpips_val]
                        f.write(','.join(map(str,row))+'\n')

            except Exception as e:
                print(f"\n[Error] {img_name} 처리 중 에러: {e}")
                import traceback
                traceback.print_exc()

    print("모든 작업 완료.")

if __name__=='__main__':
    main()
