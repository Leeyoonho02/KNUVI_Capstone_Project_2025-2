import os
import cv2
import torch
import numpy as np

from torchvision import transforms
from tqdm import tqdm

import models
import dct_manip as dm
import utils_
from utils_ import Averager, mkdir
import utils.custom_transforms as ctrans


# =========================
# Utils
# =========================
def pad_to_multiple(img, multiple=56):
    """
    Reflect-pad image so that H, W are multiples of `multiple`
    Returns padded_img, original_h, original_w
    """
    h, w, c = img.shape
    pad_h = (multiple - h % multiple) % multiple
    pad_w = (multiple - w % multiple) % multiple
    img_pad = np.pad(
        img,
        ((0, pad_h), (0, pad_w), (0, 0)),
        mode='reflect'
    )
    return img_pad, h, w


# =========================
# Path settings
# =========================
gt_path = os.path.expanduser('~/JDEC/jpeg_removal/valid_paired/valid/')
lq_base_path = os.path.expanduser('~/JDEC/jpeg_removal/valid_paired/')
model_path = os.path.expanduser('~/JDEC/checkpoints/jdec.pth')

save_root = './results'
mkdir(save_root)

quality_list = [30, 50, 70]


# =========================
# Load model
# =========================
print(f"Loading model from {model_path}...")
model_spec = torch.load(model_path)['model']
model = models.make(model_spec, load_sd=True).cuda()
model.eval()

normalize = ctrans.ToRange(
    val_min=-1, val_max=1,
    orig_min=-1024, orig_max=1016
)


# =========================
# Inference
# =========================
for q in quality_list:
    print(f'\n===== JPEG Q = {q} =====')

    lq_path = os.path.join(lq_base_path, f'valid_{q}')
    save_path = os.path.join(save_root, f'Q{q}')
    mkdir(save_path)

    res_psnr = Averager()
    res_psnr_b = Averager()
    res_ssim = Averager()
    inp_psnr = Averager()
    inp_ssim = Averager()

    img_list = sorted(os.listdir(gt_path))

    for name in tqdm(img_list):
        # ---------------------------------
        # Load GT and pad
        # ---------------------------------
        gt_img = cv2.imread(os.path.join(gt_path, name), -1)
        gt_pad, h0, w0 = pad_to_multiple(gt_img, 56)

        gt = transforms.ToTensor()(cv2.cvtColor(gt_pad, cv2.COLOR_BGR2RGB))

        # ---------------------------------
        # Load JPEG input and pad identically
        # ---------------------------------
        jpg_name = name.replace('.png', '.jpg')
        lq_img = cv2.imread(os.path.join(lq_path, jpg_name), -1)
        lq_img = lq_img[:gt_img.shape[0], :gt_img.shape[1], :]
        lq_pad, _, _ = pad_to_multiple(lq_img, 56)

        inpinp = transforms.ToTensor()(cv2.cvtColor(lq_pad, cv2.COLOR_BGR2RGB))

        # ---------------------------------
        # Read JPEG DCT coefficients (from padded JPEG)
        # ---------------------------------
        temp_jpg = './bin/temp_pad.jpg'
        mkdir('./bin')
        cv2.imwrite(
            temp_jpg,
            lq_pad,
            [int(cv2.IMWRITE_JPEG_QUALITY), q]
        )

        input_ = dm.read_coefficients(temp_jpg)

        inp_swin = input_[2]         # Y
        inp_swin_cbcr = input_[3]    # CbCr
        dqt_swin = input_[1]         # quant table

        q_y = dqt_swin[0]
        q_cbcr = dqt_swin[1]

        # de-quantization
        inp_swin = torch.clamp(inp_swin * q_y, min=-1024, max=1016)
        inp_swin_cbcr = torch.clamp(inp_swin_cbcr * q_cbcr, min=-1024, max=1016)

        # normalization
        inp_swin = normalize(inp_swin)
        inp_swin_cbcr = normalize(inp_swin_cbcr)

        dqt_swin = torch.stack([q_y, q_cbcr], dim=0)
        dqt_swin = normalize(dqt_swin)

        # ---------------------------------
        # Inference
        # ---------------------------------
        with torch.no_grad():
            pred = model(
                inp_swin.unsqueeze(0).cuda(),
                inp_swin_cbcr.unsqueeze(0).cuda(),
                dqt_swin.unsqueeze(0).cuda()
            )
            pred = pred.squeeze(0).cpu() + 0.5

        # ---------------------------------
        # Crop back to original resolution
        # ---------------------------------
        pred = pred[:, :h0, :w0]
        inpinp = inpinp[:, :h0, :w0]
        gt = gt[:, :h0, :w0]

        # ---------------------------------
        # Metrics
        # ---------------------------------
        pred_np = (pred * 255).round().clamp(0, 255) \
            .permute(1, 2, 0).numpy().astype(np.uint8)
        gt_np = (gt * 255).round().clamp(0, 255) \
            .permute(1, 2, 0).numpy().astype(np.uint8)
        inp_np = (inpinp * 255).round().clamp(0, 255) \
            .permute(1, 2, 0).numpy().astype(np.uint8)

        # Input PSNR / SSIM
        inp_psnr.add(utils_.calculate_psnr(gt_np, inp_np))
        torch_gt = transforms.ToTensor()(gt_np).unsqueeze(0)
        torch_inp = transforms.ToTensor()(inp_np).unsqueeze(0)
        inp_ssim.add(utils_.ssim_qg(torch_gt, torch_inp).item())

        # Result PSNR / PSNRB / SSIM
        res_psnr.add(utils_.calculate_psnr(gt_np, pred_np))
        res_psnr_b.add(utils_.calculate_psnrb(gt_np, pred_np))
        torch_pred = transforms.ToTensor()(pred_np).unsqueeze(0)
        res_ssim.add(utils_.ssim_qg(torch_gt, torch_pred).item())

        # ---------------------------------
        # Save result
        # ---------------------------------
        cv2.imwrite(
            os.path.join(save_path, name),
            cv2.cvtColor(pred_np, cv2.COLOR_BGR2RGB)
        )

    # ---------------------------------
    # Print results
    # ---------------------------------
    print(f'Input PSNR : {inp_psnr.item():.2f}')
    print(f'Input SSIM : {inp_ssim.item():.4f}')
    print(f'Result PSNR: {res_psnr.item():.2f}')
    print(f'Result PSNRB: {res_psnr_b.item():.2f}')
    print(f'Result SSIM: {res_ssim.item():.4f}')
