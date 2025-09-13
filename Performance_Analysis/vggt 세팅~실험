## VGGT 환경세팅

**git clone https://github.com/facebookresearch/vggt.git**

**cd vggt**

**conda create -n vggt python=3.11**

**conda activate vggt**

**pip install -r requirements.txt**

**pip install pycolmap==3.10.0**

**pip install hydra-core**

**pip install git+https://github.com/cvg/LightGlue.git**

+여기까지 하고 나중에 실행 안 되면 trimesh 설치 (아마 설치하라고 나올 거예요)

## VGGT 실험 진행

wsl이나 리눅스 환경에서 진행

**cp -r /mnt/c/Users/PC007/Desktop/dataset ~/dataset**

- > 경로는 알아서 바꾸시면 되고 wsl 홈으로 복사하는 코드 (이래야 빨라짐)

vggt는 무조건 images라는 폴더 안에 사진이 있다고 생각하기 때문에

실제 이미지들은 다 images 안에 넣어야 됨

실행할 때는 경로에 /images까지 안 넣고 그 전까지만 넣으면 됩니다

**python demo_colmap.py --scene_dir ~/dataset/interval_1 --conf_thres_value 3.0**

- > vggt 실행 코드 conf_thres_value가 confidence 값인데 작을수록 noise까지 다 잡아냄

**cp -r ~/dataset/interval_1/sparse /mnt/c/Users/PC007/Desktop/sparse_result**

- > wsl 홈에 복사해놨던 폴더 안에 결과가 생겼을 텐데 그거 다시 windows로 복사

ply 파일 cloudcompare로 열어서 보시면 됩니다
