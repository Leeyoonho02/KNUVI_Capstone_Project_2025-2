# 1. 환경 세팅

- 우분투 22.04.5, 24.04.2 둘 다 돌아가는 것 확인함
- CUDA=11.6~8 이어야 함. 아마 11이면 되는 듯

### 세팅 명령어

- **Git clone https://github.com/graphdeco-inria/gaussian-splatting.git --recursive**
	- -> GS 디렉토리로 이동
- **conda env create --file environment.yml**
	- environment.yml에서 일부 수정함
	- python=3.10.4 로 수정
	- pip 리스트에서 opencv-python을 맨 앞으로 당김

### 관련 이슈
- **CUDA 11.8**
	- 11.8은 최소 쿠다 드라이버 520을 요구함
	- gcc 버전도 10으로 맞춰야 하는데, 7번자리 개 빡치게 gcc8이 계속 살아남음

# 2. 실행 명령어

- **python train.py -s < 데이터셋 디렉토리 > --eval**
- 데이터셋 디렉토리는 다음과 같은 구조를 가져야 함
	- images (이미지 담긴 디렉토리. 무조건 이름 images여야 함)
	- sparse/0/bin 파일 세개 (images.bin 확인)
- **python render.py -m < 아웃풋 디렉토리 >
	- 렌더링 결과를 사진으로 보여줌, test 디렉토리에 있는걸로 확인
- **python metrics.py -m < 아웃풋 디렉토리 >
	- 렌더링 결과로 SSIM↑, PSNR↑, LPIPS↓ 나옴

### 참고
- GUI 뷰어 실행 실패해서 그냥 렌더링 사진으로 비교함. 보통 논문에는 이게 들어가서 상관 없을 것 같음

# 3. 자동화 코드 관련

- 리눅스에서 동작함.
- 이 코드는 반드시 아래 디렉토리 구조에서 동작함.
	- 3DGS_auto.py
	- datasets
		- 1_* (input file dir)
		- 2_*
		- 3_*
		- ...
	- gaussian-splatting
		- train.py
		- render.py
		- metrics.py
		- outputs
		- ...
- 3DGS_auto.py를 동작시키면, datasets 디렉토리 내부 input 파일 디렉토리 하나하나에 대해 아래 동작을 수행한다. (폴더 이름 맨 앞의 숫자 순서대로 실행하도록)
	- train.py 수행 (참고예시: python train.py -s ../datasets/1_* --eval)
	- gaussian-splatting/outputs에서 가장 최근에 생성된 디렉토리 이름을 데이터셋 디렉토리 이름으로 변경 (ex.93jf23fj9 -> 1_* )
	- render.py 수행 (참고예시: python render.py -m outputs/1_* )
	- metrics.py 수행 (참고예시: python metrics.py -m outputs/1_* )

---
# 결과
- 3DGS 논문에서 소수점 3자리 아래로는 절삭하여, 동일하게 표기함

## 1) JPEG

| Mip-NeRF 360     | SSIM↑ | PSNR↑  | LPIPS↓ |
| ---------------- | ----- | ------ | ------ |
| bicycle_8down    | 0.811 | 25.842 | 0.149  |
| bicycle_8down_90 | 0.787 | 25.464 | 0.166  |
| bicycle_8down_70 | 0.774 | 25.366 | 0.190  |
| bicycle_8down_50 | 0.753 | 25.041 | 0.215  |
| bicycle_8down_30 | 0.734 | 24.889 | 0.251  |
| bicycle_8down_10 | 0.646 | 23.446 | 0.398  |

| Mip-NeRF 360    | SSIM↑ | PSNR↑  | LPIPS↓ |
| --------------- | ----- | ------ | ------ |
| garden_8down    | 0.911 | 28.946 | 0.066  |
| garden_8down_90 | 0.882 | 28.103 | 0.093  |
| garden_8down_70 | 0.854 | 27.380 | 0.134  |
| garden_8down_50 | 0.838 | 27.177 | 0.159  |
| garden_8down_30 | 0.812 | 26.647 | 0.195  |
| garden_8down_10 | 0.728 | 25.249 | 0.337  |
