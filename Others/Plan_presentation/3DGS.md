# 3DGS
### 논문
https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/



### 3D Gaussian
3D Gaussian은 3차원 공간에서 반 투명한 공처럼 표현됨!



### 3D Gaussian Splatting
여러 Multi-view 영상(이미지, 동영상)을 받아 그 장면을 수많은 3D Gaussian(반 투명 공)을 점묘화처럼 쌓아올려 3차원 장면을 표현하는 기술, 복잡한 3D 공간도 빠르고 자연스럽게 화면에 렌더링 가능



### input/Output
Input   : Multi-view(여러 각도에서 찍은) 이미지, 동영상

output : 수백 ~ 수천만 개의 3D Gaussian 들의 정보

gaussian 은 다음과 같은 정보들로 이루어져있음
| Mean | 3D 공간상의 좌표(공의 중심점) |
| --- | --- |
| Covariance  | 각 가우시안이 타원체로 퍼지는 정도와 방향(공의 크기와 방향) |
| Color | 각 가우시안의 RGB 값(공의 색상) |
| Opacity | 투명도/밀도 |



### Process
1. 렌더링 하고자 하는 공간의 사진을 여러 각도에서 촬영 후 SfM으로 공간의 특징적인 포인트를 추출하고 그 위치를 계산함
2. 해당 위치에 임의의 크기, 방향, 색상, 투명도로 초기화된 3D Gaussian 들을 뿌리고 2D 이미지 공간으로 Projection(투영)
3. 3D Gaussian들의 조합이 어느 방향에서 보더라도 주어진 영상과 같아지도록 3D Gaussian들을 조정하는 과정을 반복



### 장단점
장점 : 기존 렌더링 모델인 NeRF는 한 장면을 그려내는 데에 2일이 걸릴만큼 엄청 오래 걸림. 3DGS는 30분(light 버전으론 5분)정도면 한 장면을 생성할 수 있을만큼 빠름.

단점 : 깔끔한 렌더링을 위해선 많은 이미지가 필요함 

-> 이런 부분을 VGGT에서 개선
