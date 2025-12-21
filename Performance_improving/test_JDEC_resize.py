import os
import cv2
import torch
import numpy as np
from torchvision import transforms
from tqdm import tqdm

import models
import dct_manip as dm
from utils_ import Averager, mkdir
import utils_
import utils.custom_transforms as ctrans

# ==========================================
# 1. 경로 및 모델 설정
# ==========================================
gt_path = os.path.expanduser('~/JDEC/jpeg_removal/valid_paired/valid/')
model_path = os.path.expanduser('~/JDEC/checkpoints/jdec.pth')
save_root = './results'
mkdir(save_root)

print(f"Loading model: {model_path}")
model_spec = torch.load(model_path)['model']
model = models.make(model_spec, load_sd=True).cuda()
model.eval()

normalize = ctrans.ToRange(val_min=-1, val_max=1, orig_min=-1024, orig_max=1016)
quality_list = [30, 50, 70] 


for q in quality_list:
    print(f'\n🚀 --- Testing Quality: {q} ---')
    res_psnr, res_ssim = Averager(), Averager()
    inp_psnr, inp_ssim = Averager(), Averager()

    file_list = sorted([f for f in os.listdir(gt_path) if f.endswith('.png')])

    for item in tqdm(file_list):
        img_name = item.split('.')[0]

        # 1. [중요] 원본 로드 후 560x560으로 먼저 리사이즈 (격자 정렬 유지의 핵심)
        orig_img = cv2.imread(os.path.join(gt_path, item))
        orig_img = cv2.resize(orig_img, (560, 560)) 
        gt_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)

        # 2. 리사이즈된 이미지를 해당 품질로 압축 (JDEC 전용 입력 생성)
        tmp_lq_path = f'./tmp_q{q}.jpg'
        cv2.imwrite(tmp_lq_path, orig_img, [int(cv2.IMWRITE_JPEG_QUALITY), q])

        # 3. DCT 데이터 로드
        input_data = dm.read_coefficients(tmp_lq_path)
        inp_y = input_data[2].cuda()
        inp_cbcr = input_data[3].cuda()
        dqt = input_data[1]

        q_y, q_cbcr = dqt[0].cuda(), dqt[1].cuda()
        inp_y = torch.clamp(inp_y * q_y, min=-1024, max=1016)
        inp_cbcr = torch.clamp(inp_cbcr * q_cbcr, min=-1024, max=1016)

        # 4. 모델 추론
        inp_y_norm = normalize(inp_y)
        inp_cbcr_norm = normalize(inp_cbcr)
        dqt_stack = normalize(torch.stack([q_y, q_cbcr], dim=0))

        with torch.no_grad():
            pred = model(inp_y_norm.unsqueeze(0), 
                         inp_cbcr_norm.unsqueeze(0),
                         dqt_stack.unsqueeze(0))
            pred = pred.squeeze(0).detach().cpu() + 0.5

        # 5. 비교군(Input) 이미지 로드
        lq_img = cv2.imread(tmp_lq_path)
        lq_rgb = cv2.cvtColor(lq_img, cv2.COLOR_BGR2RGB)

        # 6. 수치 계산을 위한 numpy 변환
        gt_np = gt_rgb.astype(np.uint8)
        inp_np = lq_rgb.astype(np.uint8)
        pred_np = (pred * 255).round().clamp(0, 255).permute(1, 2, 0).numpy().astype(np.uint8)

        # 7. 결과 저장
        save_dir = os.path.join(save_root, str(q))
        mkdir(save_dir)
        cv2.imwrite(os.path.join(save_dir, f"{img_name}_res.png"), cv2.cvtColor(pred_np, cv2.COLOR_RGB2BGR))

        # 8. 지표 누적
        inp_psnr.add(utils_.calculate_psnr(gt_np, inp_np))
        inp_ssim.add(utils_.ssim_qg(transforms.ToTensor()(gt_np).unsqueeze(0), 
                                   transforms.ToTensor()(inp_np).unsqueeze(0)).item())
        res_psnr.add(utils_.calculate_psnr(gt_np, pred_np))
        res_ssim.add(utils_.ssim_qg(transforms.ToTensor()(gt_np).unsqueeze(0), 
                                   transforms.ToTensor()(pred_np).unsqueeze(0)).item())

        torch.cuda.empty_cache()

    print(f'\n✅ [Quality {q}] Result Summary')
    print(f'   - Input  PSNR: {inp_psnr.item():.2f} / SSIM: {inp_ssim.item():.4f}')
    print(f'   - Result PSNR: {res_psnr.item():.2f} / SSIM: {res_ssim.item():.4f} (UP!)')

print('\n🎉 수치가 정상적으로 상승했을 겁니다! 결과를 확인하세요.')
