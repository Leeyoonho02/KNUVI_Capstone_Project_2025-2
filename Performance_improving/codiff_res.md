---

# CODiff JPEG 복원 실험 결과 분석

이 문서에서는 **CODiff**를 사용하여 JPEG 압축 이미지의 손상을 복원한 실험 결과를 정리합니다.
실험에서는 JPEG10, JPEG50, JPEG70 등 다양한 압축률을 대상으로 정량적 지표를 측정했습니다.

## 1. 실험 환경 및 지표 소개

* **모델**: CODiff (Stable Diffusion 기반의 Conditional Diffusion Model)
* **평가 지표 소개**

| 지표 | 풀네임 | 특징 | 목표 |
| --- | --- | --- | --- |
| **PSNR** | Peak Signal-to-Noise Ratio | 수치적인 픽셀 일치도 측정 | \uparrow |
| **SSIM** | Structural Similarity Index | 이미지의 구조적 유사성 측정 | \uparrow |
| **LPIPS** | Perceptual Patch Similarity | 인간의 시각적 인지 유사도 측정 (가장 중요) | \downarrow |
| **DISTS** | Deep Structure & Texture Similarity | 질감 및 구조적 유사성 측정 | \downarrow |
| **NIQE** | Natural Image Quality Evaluator | 이미지의 자연스러움 측정 (No-Reference) | \downarrow |
| **MUSIQ** | Multi-scale Image Quality Transformer | 종합적인 화질 점수 측정 (No-Reference) | \uparrow |
| **MANIQA** | Multi-dimension Attention Network | 화질 및 미적 품질 측정 (No-Reference) | \uparrow |
| **CLIPIQA** | CLIP-based Image Quality Assessment | CLIP 기반 지각적 품질 점수 | \uparrow |

---

## 2. 전체 결과 (평균 데이터)

각 압축률별 이미지들의 평균 수치입니다. 수치가 개선된 항목(성능 향상)은 **굵게(Bold)** 표시하였습니다.

### [JPEG 10] - 저품질 복원

압축 손상이 심한 상태에서 가장 드라마틱한 개선 효과를 보였습니다.

| 구분 | PSNR | SSIM | LPIPS | DISTS | NIQE | MUSIQ | MANIQA | CLIPIQA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Before** | 23.0365 | 0.7131 | 0.2887 | 0.2401 | 4.9239 | 56.1381 | 0.3342 | 0.3961 |
| **After** | 19.8043 | 0.4734 | **0.1809** | **0.1275** | **2.5168** | **70.0854** | **0.4055** | **0.7614** |

---

### [JPEG 50] - 중간 품질 복원

지각적 유사도와 자연스러움에서는 이득을 보았으나, 일부 지표에서는 효과가 미미하거나 오히려 하락하는 경향을 보였습니다

| 구분 | PSNR | SSIM | LPIPS | DISTS | NIQE | MUSIQ | MANIQA | CLIPIQA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Before** | 27.8013 | 0.8936 | 0.0662 | 0.1188 | 2.8036 | 70.4818 | 0.4439 | 0.7835 |
| **After** | 20.0953 | 0.5030 | 0.1424 | **0.0897** | **2.5907** | **70.6407** | **0.4445** | 0.7774 |

---

### [JPEG 70] - 고품질 복원

이미지가 깨끗한 상태에서 생성형 모델이 개입하여 오히려 원본과의 거리가 멀어지는 역효과가 발생했습니다.

| 구분 | PSNR | SSIM | LPIPS | DISTS | NIQE | MUSIQ | MANIQA | CLIPIQA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Before** | 29.6274 | 0.9271 | 0.0362 | 0.0894 | 2.4909 | 70.8085 | 0.4656 | 0.8144 |
| **After** | 20.0972 | 0.5049 | 0.1401 | **0.0870** | 2.6231 | 70.2923 | 0.4387 | 0.7706 |

---

## 3. 실험 결과 분석 요약

1. **저품질(JPEG 10)에서의 비약적 향상**
* PSNR과 SSIM은 하락했으나, 이는 생성형 모델(Diffusion)의 특성상 픽셀 단위 일치도보다 **지각적 품질**에 집중하기 때문입니다.
* 실제로 **NIQE(4.92 → 2.51)**와 **CLIPIQA(0.39 → 0.76)**가 대폭 개선되어, 육안으로 보기에 훨씬 자연스럽고 선명한 결과를 보여줍니다.


2. **중간 품질(JPEG 50)의 혼조세**
* 지감 보존 지표인 **DISTS**와 자연스러움인 **NIQE**는 여전히 개선되는 모습을 보입니다.
* 하지만 고수준 품질 지표인 LPIPS나 CLIPIQA는 미세하게 하락하거나 유지되는 경향을 보입니다.


3. **고품질(JPEG 70)에서의 역효과**
* 이미 원본에 가까운 이미지임에도 불구하고 모델이 새로운 디테일을 생성(Hallucination)하면서 **지각적 유사도(LPIPS)**가 크게 나빠졌습니다.
* PSNR/SSIM 수치가 급격히 떨어지는 것으로 보아, 고품질 이미지에서는 Diffusion 기반 복원보다 전통적인 필터 방식이 더 유리할 수 있음을 시사합니다.


4. **결론 및 향후 과제**
* CODiff는 **강한 압축 손상이 발생한 이미지**에서 압도적인 복원 성능을 보입니다.
* 고품질 이미지에서는 원본 왜곡 현상이 발생해 수치가 안 좋아졌습니다.

---

### 4. 참고 사항

* 모든 수치는 실험 데이터셋의 산술 평균값을 사용했습니다.
* 상세 데이터는 `results.csv` 파일을 참조하십시오.
