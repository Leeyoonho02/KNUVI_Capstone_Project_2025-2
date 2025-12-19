import os
import cv2
import torch
import numpy as np
import torch.nn.functional as F
from torchvision import transforms
from tqdm import tqdm

import models
import dct_manip as dm
from utils_ import Averager, mkdir
import utils_
import utils.custom_transforms as ctrans

# ==========================================
# 1. 경로 및 설정 (기존 설정 유지)
# ==========================================
gt_path = os.path.expanduser('~/JDEC/jpeg_removal/valid_paired/valid/')
lq_base_path = os.path.expanduser('~/JDEC/jpeg_removal/valid_paired/valid_')
model_path = os.path.expanduser('~/JDEC/checkpoints/jdec.pth')
save_root = './results'
mkdir(save_root)

# 모델 로드
print(f"Loading model from {model_path}...")
model_spec = torch.load(model_path)['model']
model = models.make(model_spec, load_sd=True).cuda()
model.eval()

normalize = ctrans.ToRange(val_min=-1, val_max=1, orig_min=-1024, orig_max=1016)
quality_list = [30, 50, 70] 

for q in quality_list:
    lq_path = lq_base_path + str(q) + '/'
    print(f'\n🚀 --- Testing Quality: {q} (Reading from {lq_path}) ---')
    
    inp_psnr, inp_ssim = Averager(), Averager()
    res_psnr, res_psnr_b, res_ssim = Averager(), Averager(), Averager()

    # GT 폴더 기준으로 파일 리스트 확보
    file_list = sorted([f for f in os.listdir(gt_path) if f.endswith('.png')])

    for item in tqdm(file_list):
        img_name = item.split('.')[0]
        gt_img_path = os.path.join(gt_path, item)
        lq_img_path = os.path.join(lq_path, img_name + '.jpg')

        if not os.path.exists(lq_img_path):
            continue

        # 1. 이미지 로드 및 560x560 리사이즈 (OOM 및 배수 에러 동시 해결)
        gt_cv = cv2.imread(gt_img_path)
        gt_cv = cv2.resize(gt_cv, (560, 560)) # 56의 배수
        gt_rgb = cv2.cvtColor(gt_cv, cv2.COLOR_BGR2RGB)
        
        lq_cv = cv2.imread(lq_img_path)
        lq_cv = cv2.resize(lq_cv, (560, 560)) # GT와 크기 일치
        
        # [중요] JDEC은 파일에서 DCT를 직접 뽑으므로, 리사이즈된 이미지를 임시 저장 후 읽어야 함
        tmp_lq_path = './tmp_resized_lq.jpg'
        cv2.imwrite(tmp_lq_path, lq_cv, [int(cv2.IMWRITE_JPEG_QUALITY), 100]) # 품질 100으로 임시 저장

        # 2. DCT 데이터 추출
        input_data = dm.read_coefficients(tmp_lq_path)
        inp_y = input_data[2]
        inp_cbcr = input_data[3]
        dqt = input_data[1]
        
        q_y, q_cbcr = dqt[0].cuda(), dqt[1].cuda()
        inp_y = torch.clamp(inp_y.cuda() * q_y, min=-1024, max=1016)
        inp_cbcr = torch.clamp(inp_cbcr.cuda() * q_cbcr, min=-1024, max=1016)

        # 3. 모델 추론
        inp_y_norm = normalize(inp_y)
        inp_cbcr_norm = normalize(inp_cbcr)
        dqt_stack = normalize(torch.stack([q_y, q_cbcr], dim=0))

        with torch.no_grad():
            pred = model(inp_y_norm.unsqueeze(0), 
                         inp_cbcr_norm.unsqueeze(0),
                         dqt_stack.unsqueeze(0))
            pred = pred.squeeze(0).detach().cpu() + 0.5

        # 4. 결과 이미지 저장
        pred_np = (pred * 255).round().clamp(0, 255).permute(1, 2, 0).numpy().astype(np.uint8)
        save_dir = os.path.join(save_root, str(q))
        mkdir(save_dir)
        cv2.imwrite(os.path.join(save_dir, img_name + '_restored.png'), 
                    cv2.cvtColor(pred_np, cv2.COLOR_RGB2BGR))

        # 5. 수치 계산 (리사이즈된 GT와 비교)
        inp_np = cv2.cvtColor(lq_cv, cv2.COLOR_BGR2RGB)
        gt_np = gt_rgb

        inp_psnr.add(utils_.calculate_psnr(gt_np, inp_np))
        inp_ssim.add(utils_.ssim_qg(transforms.ToTensor()(gt_np).unsqueeze(0), 
                                   transforms.ToTensor()(inp_np).unsqueeze(0)).item())
        res_psnr.add(utils_.calculate_psnr(gt_np, pred_np))
        res_ssim.add(utils_.ssim_qg(transforms.ToTensor()(gt_np).unsqueeze(0), 
                                   transforms.ToTensor()(pred_np).unsqueeze(0)).item())
        
        torch.cuda.empty_cache()

    # 최종 결과 출력
    print(f'\n✅ [Quality {q}] Average Results')
    print(f'   - Input  PSNR: {inp_psnr.item():.2f} / SSIM: {inp_ssim.item():.4f}')
    print(f'   - Result PSNR: {res_psnr.item():.2f} / SSIM: {res_ssim.item():.4f}')

print('\n🎉 테스트 완료! ~/JDEC/results 폴더에서 결과 이미지를 확인하세요.')
